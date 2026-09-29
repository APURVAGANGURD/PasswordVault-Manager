# modules/team_backend.py

import sys
import os

sys.path.append(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from database.models import (
    User,
    Organization,
    Department,
    Team,
    TeamMember,
    Password,
    Share,
    Vault,
)


# ============================================================
# USER HELPERS
# ============================================================

def get_user_id(user):
    if user is None:
        return None

    if isinstance(user, dict):
        return user.get("id")

    return getattr(user, "id", None)


def get_user_email(user):
    if user is None:
        return None

    if isinstance(user, dict):
        email = user.get("email")
    else:
        email = getattr(user, "email", None)

    if email:
        return email.strip().lower()

    return None


def get_user_role(user):
    if user is None:
        return ""

    if isinstance(user, dict):
        role = user.get("role")
    else:
        role = getattr(user, "role", None)

    if role is None:
        return ""

    # Handles both:
    # ADMIN
    # Role.ADMIN
    # UserRole.ADMIN
    role = str(role).upper().strip()

    if "." in role:
        role = role.split(".")[-1]

    return role


def is_admin(user):
    return get_user_role(user) in {"ADMIN", "OWNER"}


def is_manager(user):
    return get_user_role(user) == "MANAGER"


def is_employee(user):
    return get_user_role(user) in {
        "USER",
        "EMPLOYEE",
        "PERSONAL_USER",
    }


def can_manage_members(user):
    return get_user_role(user) in {
        "ADMIN",
        "OWNER",
        "MANAGER",
    }


# ============================================================
# FIND USER
# ============================================================

def find_user_by_email(db, email):
    if not email:
        return None

    email = email.strip().lower()

    return (
        db.query(User)
        .filter(User.email.ilike(email))
        .first()
    )


# ============================================================
# GET USER ORGANIZATION
# ============================================================

def get_user_organization(db, user):

    user_id = get_user_id(user)
    user_email = get_user_email(user)

    # --------------------------------------------------------
    # 1. Try organization_name from session user
    # --------------------------------------------------------

    org_name = ""

    if isinstance(user, dict):
        org_name = user.get("organization_name", "")
    else:
        org_name = getattr(
            user,
            "organization_name",
            ""
        )

    if org_name:

        organization = (
            db.query(Organization)
            .filter(
                Organization.name == org_name
            )
            .first()
        )

        if organization:
            return organization

    # --------------------------------------------------------
    # 2. Organization owned by user
    # --------------------------------------------------------

    if user_id:

        organization = (
            db.query(Organization)
            .filter(
                Organization.owner_id == user_id
            )
            .first()
        )

        if organization:
            return organization

    # --------------------------------------------------------
    # 3. Organization through TeamMember
    # --------------------------------------------------------

    membership_query = (
        db.query(TeamMember)
        .join(
            Team,
            Team.id == TeamMember.team_id
        )
        .filter(
            Team.organization_id.isnot(None)
        )
    )

    conditions = []

    if user_id:
        conditions.append(
            TeamMember.user_id == user_id
        )

    if user_email:
        conditions.append(
            TeamMember.email.ilike(user_email)
        )

    if not conditions:
        return None

    membership = (
        membership_query
        .filter(or_(*conditions))
        .first()
    )

    if membership:

        team = (
            db.query(Team)
            .filter(
                Team.id == membership.team_id
            )
            .first()
        )

        if team and team.organization_id:

            return (
                db.query(Organization)
                .filter(
                    Organization.id
                    == team.organization_id
                )
                .first()
            )

    return None


# ============================================================
# DEPARTMENTS
# ============================================================

def get_departments(
    db,
    organization_id=None,
    user=None
):

    if user:

        organization = get_user_organization(
            db,
            user
        )

        if organization:
            organization_id = organization.id

    if not organization_id:
        return []

    return (
        db.query(Department)
        .filter(
            Department.organization_id
            == organization_id
        )
        .order_by(
            Department.name.asc()
        )
        .all()
    )


# ============================================================
# GET USER TEAMS
# ============================================================

def get_user_teams(
    db,
    user,
    organization_id
):

    user_id = get_user_id(user)
    user_email = get_user_email(user)

    if not organization_id:
        return []

    # --------------------------------------------------------
    # ADMIN / OWNER
    # Can see every team in their organization
    # --------------------------------------------------------

    if is_admin(user):

        return (
            db.query(Team)
            .options(
                joinedload(Team.department),
                joinedload(
                    Team.members
                ).joinedload(
                    TeamMember.user
                ),
            )
            .filter(
                Team.organization_id
                == organization_id
            )
            .order_by(
                Team.created_at.desc()
            )
            .all()
        )

    # --------------------------------------------------------
    # MANAGER / EMPLOYEE
    # Only teams where user is a member
    # --------------------------------------------------------

    conditions = []

    if user_id:
        conditions.append(
            TeamMember.user_id == user_id
        )

    if user_email:
        conditions.append(
            TeamMember.email.ilike(user_email)
        )

    if not conditions:
        return []

    return (
        db.query(Team)
        .join(
            TeamMember,
            TeamMember.team_id == Team.id
        )
        .options(
            joinedload(Team.department),
            joinedload(
                Team.members
            ).joinedload(
                TeamMember.user
            ),
        )
        .filter(
            Team.organization_id
            == organization_id
        )
        .filter(
            or_(*conditions)
        )
        .order_by(
            Team.created_at.desc()
        )
        .distinct()
        .all()
    )


# ============================================================
# CREATE TEAM
# ============================================================

def create_team(
    db,
    user,
    team_name,
    department_id=None,
    description=None
):
    """
    Create a new team.

    Only ADMIN / OWNER can create teams.

    Parameters:
        db              SQLAlchemy session
        user            Logged-in user
        team_name       Team name
        department_id   Optional department ID
        description     Optional team description
    """

    try:

        # ----------------------------------------------------
        # Permission
        # ----------------------------------------------------

        if not is_admin(user):
            return (
                False,
                "Only administrators can create teams."
            )

        # ----------------------------------------------------
        # Current user
        # ----------------------------------------------------

        user_id = get_user_id(user)

        if not user_id:
            return (
                False,
                "Logged-in user ID could not be determined."
            )

        # ----------------------------------------------------
        # Organization
        # ----------------------------------------------------

        organization = get_user_organization(
            db,
            user
        )

        if not organization:
            return (
                False,
                "You are not associated with an organization."
            )

        # ----------------------------------------------------
        # Team name
        # ----------------------------------------------------

        team_name = (
            team_name or ""
        ).strip()

        if not team_name:
            return (
                False,
                "Team name is required."
            )

        # ----------------------------------------------------
        # Description
        # ----------------------------------------------------

        description = (
            description or ""
        ).strip()

        if not description:
            description = None

        # ----------------------------------------------------
        # Duplicate team check
        # ----------------------------------------------------

        existing_team = (
            db.query(Team)
            .filter(
                Team.organization_id
                == organization.id
            )
            .filter(
                Team.team_name.ilike(team_name)
            )
            .first()
        )

        if existing_team:
            return (
                False,
                "A team with this name already exists."
            )

        # ----------------------------------------------------
        # Department validation
        # ----------------------------------------------------

        if department_id is not None:

            department = (
                db.query(Department)
                .filter(
                    Department.id
                    == department_id
                )
                .filter(
                    Department.organization_id
                    == organization.id
                )
                .first()
            )

            if not department:
                return (
                    False,
                    "Selected department does not belong to your organization."
                )

        # ----------------------------------------------------
        # CREATE TEAM
        # ----------------------------------------------------

        team = Team(
            team_name=team_name,
            description=description,
            department_id=department_id,
            organization_id=organization.id,
            created_by=user_id,
        )

        db.add(team)

        db.commit()

        db.refresh(team)

        return (
            True,
            team
        )

    except Exception as exc:

        db.rollback()

        return (
            False,
            str(exc)
        )


# ============================================================
# ADD TEAM MEMBER
# ============================================================

def add_team_member(
    db,
    user,
    team_id,
    email,
    role="EMPLOYEE"
):

    try:

        if not can_manage_members(user):
            return (
                False,
                "You do not have permission to add members."
            )

        current_user_id = get_user_id(user)

        if not current_user_id:
            return (
                False,
                "Logged-in user could not be identified."
            )

        email = (
            email or ""
        ).strip().lower()

        if not email:
            return (
                False,
                "Member email is required."
            )

        role = (
            role or "EMPLOYEE"
        ).upper().strip()

        if role == "USER":
            role = "EMPLOYEE"

        if role not in {
            "MANAGER",
            "EMPLOYEE"
        }:
            return (
                False,
                "Invalid team member role."
            )

        # ----------------------------------------------------
        # Team
        # ----------------------------------------------------

        team = (
            db.query(Team)
            .filter(
                Team.id == team_id
            )
            .first()
        )

        if not team:
            return (
                False,
                "Team not found."
            )

        # ----------------------------------------------------
        # Organization
        # ----------------------------------------------------

        organization = get_user_organization(
            db,
            user
        )

        if not organization:
            return (
                False,
                "Organization not found."
            )

        if team.organization_id != organization.id:
            return (
                False,
                "You cannot modify a team from another organization."
            )

        # ----------------------------------------------------
        # User
        # ----------------------------------------------------

        member_user = find_user_by_email(
            db,
            email
        )

        if not member_user:

            return (
                False,
                f"No registered user found with email: {email}"
            )

        # ----------------------------------------------------
        # Duplicate membership
        # ----------------------------------------------------

        existing = (
            db.query(TeamMember)
            .filter(
                TeamMember.team_id
                == team_id
            )
            .filter(
                or_(
                    TeamMember.user_id
                    == member_user.id,
                    TeamMember.email.ilike(email),
                )
            )
            .first()
        )

        if existing:
            return (
                False,
                "This user is already a member of the team."
            )

        # ----------------------------------------------------
        # Create member
        # ----------------------------------------------------

        member = TeamMember(
            team_id=team.id,
            user_id=member_user.id,
            email=member_user.email,
            role=role,
        )

        db.add(member)

        db.commit()

        db.refresh(member)

        return (
            True,
            "Member added successfully."
        )

    except Exception as exc:

        db.rollback()

        return (
            False,
            str(exc)
        )


# ============================================================
# UPDATE MEMBER ROLE
# ============================================================

def update_member_role(
    db,
    user,
    team_id,
    member_id,
    role
):

    try:

        if not can_manage_members(user):
            return (
                False,
                "You do not have permission to change member roles."
            )

        role = (
            role or ""
        ).upper().strip()

        if role == "USER":
            role = "EMPLOYEE"

        if role not in {
            "MANAGER",
            "EMPLOYEE"
        }:
            return (
                False,
                "Invalid role."
            )

        team = (
            db.query(Team)
            .filter(
                Team.id == team_id
            )
            .first()
        )

        if not team:
            return (
                False,
                "Team not found."
            )

        organization = get_user_organization(
            db,
            user
        )

        if (
            not organization
            or team.organization_id
            != organization.id
        ):
            return (
                False,
                "You cannot modify this team."
            )

        member = (
            db.query(TeamMember)
            .filter(
                TeamMember.id
                == member_id
            )
            .filter(
                TeamMember.team_id
                == team_id
            )
            .first()
        )

        if not member:
            return (
                False,
                "Team member not found."
            )

        member.role = role

        db.commit()

        return (
            True,
            "Member role updated successfully."
        )

    except Exception as exc:

        db.rollback()

        return (
            False,
            str(exc)
        )


# ============================================================
# REMOVE TEAM MEMBER
# ============================================================

def remove_team_member(
    db,
    user,
    team_id,
    member_id
):

    try:

        if not can_manage_members(user):
            return (
                False,
                "You do not have permission to remove team members."
            )

        team = (
            db.query(Team)
            .filter(
                Team.id == team_id
            )
            .first()
        )

        if not team:
            return (
                False,
                "Team not found."
            )

        organization = get_user_organization(
            db,
            user
        )

        if (
            not organization
            or team.organization_id
            != organization.id
        ):
            return (
                False,
                "You cannot modify this team."
            )

        member = (
            db.query(TeamMember)
            .filter(
                TeamMember.id
                == member_id
            )
            .filter(
                TeamMember.team_id
                == team_id
            )
            .first()
        )

        if not member:
            return (
                False,
                "Team member not found."
            )

        db.delete(member)

        db.commit()

        return (
            True,
            "Member removed successfully."
        )

    except Exception as exc:

        db.rollback()

        return (
            False,
            str(exc)
        )


# ============================================================
# DELETE TEAM
# ============================================================

def delete_team(
    db,
    user,
    team_id
):

    try:

        if not can_manage_members(user):
            return (
                False,
                "You do not have permission to delete teams."
            )

        team = (
            db.query(Team)
            .filter(
                Team.id == team_id
            )
            .first()
        )

        if not team:
            return (
                False,
                "Team not found."
            )

        organization = get_user_organization(
            db,
            user
        )

        if (
            not organization
            or team.organization_id
            != organization.id
        ):
            return (
                False,
                "You cannot delete this team."
            )

        # ----------------------------------------------------
        # Delete shares belonging to team
        # ----------------------------------------------------

        db.query(Share).filter(
            Share.team_id == team_id
        ).delete(
            synchronize_session=False
        )

        # ----------------------------------------------------
        # Delete team
        # ----------------------------------------------------

        db.delete(team)

        db.commit()

        return (
            True,
            "Team deleted successfully."
        )

    except Exception as exc:

        db.rollback()

        return (
            False,
            str(exc)
        )


# ============================================================
# GET ALL PASSWORDS
# ============================================================

def get_all_passwords(db, user):

    user_vault = (
        db.query(Vault)
        .filter(
            Vault.owner_id
            == get_user_id(user)
        )
        .first()
    )

    if not user_vault and is_admin(user):

        user_vault = (
            db.query(Vault)
            .first()
        )

    if not user_vault:
        return []

    return (
        db.query(Password)
        .filter(
            Password.vault_id
            == user_vault.id
        )
        .all()
    )


# ============================================================
# SHARE PASSWORD WITH USER
# ============================================================

def share_password_with_user(
    db,
    user,
    password_id,
    target_email,
    permission="VIEW"
):

    try:

        sender_id = get_user_id(user)

        if not sender_id:
            return (
                False,
                "Logged-in user could not be identified."
            )

        target_user = find_user_by_email(
            db,
            target_email
        )

        if not target_user:
            return (
                False,
                "No user found with this email address."
            )

        if target_user.id == sender_id:
            return (
                False,
                "You cannot share a password with yourself."
            )

        password = (
            db.query(Password)
            .filter(
                Password.id == password_id
            )
            .first()
        )

        if not password:
            return (
                False,
                "Password not found."
            )

        permission = (
            permission or "VIEW"
        ).upper().strip()

        if permission not in {
            "VIEW",
            "EDIT"
        }:
            return (
                False,
                "Invalid permission."
            )

        existing_share = (
            db.query(Share)
            .filter(
                Share.password_id
                == password_id,
                Share.sender_id
                == sender_id,
                Share.receiver_id
                == target_user.id,
                Share.team_id.is_(None),
            )
            .first()
        )

        if existing_share:
            return (
                False,
                "Password is already shared with this user."
            )

        new_share = Share(
            password_id=password_id,
            sender_id=sender_id,
            receiver_id=target_user.id,
            team_id=None,
            permission=permission,
        )

        db.add(new_share)

        db.commit()

        return (
            True,
            "Password shared with user successfully!"
        )

    except Exception as exc:

        db.rollback()

        return (
            False,
            str(exc)
        )


# ============================================================
# SHARE PASSWORD WITH TEAM
# ============================================================

def share_password_with_team(
    db,
    user,
    password_id,
    team_id,
    permission="VIEW"
):

    try:

        user_id = get_user_id(user)

        if not user_id:
            return (
                False,
                "Logged-in user could not be identified."
            )

        team = (
            db.query(Team)
            .filter(
                Team.id == team_id
            )
            .first()
        )

        if not team:
            return (
                False,
                "Team not found."
            )

        organization = get_user_organization(
            db,
            user
        )

        if not organization:
            return (
                False,
                "Organization not found."
            )

        if team.organization_id != organization.id:
            return (
                False,
                "You cannot share with a team from another organization."
            )

        password = (
            db.query(Password)
            .filter(
                Password.id
                == password_id
            )
            .first()
        )

        if not password:
            return (
                False,
                "Password not found."
            )

        permission = (
            permission or "VIEW"
        ).upper().strip()

        if permission not in {
            "VIEW",
            "EDIT"
        }:
            return (
                False,
                "Invalid permission."
            )

        existing_team_share = (
            db.query(Share)
            .filter(
                Share.password_id
                == password_id,
                Share.sender_id
                == user_id,
                Share.team_id
                == team_id,
            )
            .first()
        )

        if existing_team_share:
            return (
                False,
                "This password is already shared with this team."
            )

        team_share = Share(
            password_id=password_id,
            sender_id=user_id,
            receiver_id=None,
            team_id=team_id,
            permission=permission,
        )

        db.add(team_share)

        db.commit()

        db.refresh(team_share)

        return (
            True,
            "Password shared with team successfully!"
        )

    except Exception as exc:

        db.rollback()

        return (
            False,
            str(exc)
        )


# ============================================================
# EDIT SHARED PASSWORD
# ============================================================

def update_shared_password(
    db,
    user,
    password_id,
    new_password=None,
    new_username=None,
    new_title=None
):

    try:

        password = (
            db.query(Password)
            .filter(
                Password.id
                == password_id
            )
            .first()
        )

        if not password:
            return (
                False,
                "Password not found."
            )

        current_user_id = get_user_id(user)

        # ----------------------------------------------------
        # Check password owner
        # ----------------------------------------------------

        vault = (
            db.query(Vault)
            .filter(
                Vault.id
                == password.vault_id
            )
            .first()
        )

        if (
            vault
            and vault.owner_id
            == current_user_id
        ):

            # Owner can edit
            pass

        elif is_admin(user):

            # Admin / Owner can edit
            pass

        else:

            has_edit = False

            # ------------------------------------------------
            # Direct share
            # ------------------------------------------------

            direct_share = (
                db.query(Share)
                .filter(
                    Share.password_id
                    == password_id,
                    Share.receiver_id
                    == current_user_id,
                    Share.permission
                    == "EDIT",
                    Share.team_id.is_(None),
                )
                .first()
            )

            if direct_share:
                has_edit = True

            # ------------------------------------------------
            # Team share
            # ------------------------------------------------

            if not has_edit:

                user_teams = (
                    db.query(TeamMember)
                    .filter(
                        TeamMember.user_id
                        == current_user_id
                    )
                    .all()
                )

                team_ids = [
                    team.team_id
                    for team in user_teams
                ]

                if team_ids:

                    team_share = (
                        db.query(Share)
                        .filter(
                            Share.password_id
                            == password_id,
                            Share.team_id.in_(
                                team_ids
                            ),
                            Share.permission
                            == "EDIT",
                        )
                        .first()
                    )

                    if team_share:
                        has_edit = True

            if not has_edit:

                return (
                    False,
                    "You do not have EDIT permission for this password."
                )

        # ----------------------------------------------------
        # Update encrypted password
        # ----------------------------------------------------

        if new_password is not None:

            from security.encryption import VaultEncryption
            from security.key_manager import KeyManager

            GLOBAL_KEY = (
                KeyManager.derive_key(
                    "FIXED_KEY_123",
                    "FIXED_SALT_123"
                )
            )

            encrypted_pw, nonce = (
                VaultEncryption.encrypt_data(
                    new_password,
                    GLOBAL_KEY
                )
            )

            password.encrypted_password = encrypted_pw
            password.encryption_nonce = nonce

        # ----------------------------------------------------
        # Username
        # ----------------------------------------------------

        if new_username is not None:
            password.username = new_username

        # ----------------------------------------------------
        # Title
        # ----------------------------------------------------

        if new_title is not None:
            password.title = new_title

        db.commit()

        return (
            True,
            "Password updated successfully!"
        )

    except Exception as exc:

        db.rollback()

        return (
            False,
            str(exc)
        )


# ============================================================
# GET TEAM VAULT PASSWORDS
# ============================================================

def get_team_vault_passwords(
    db,
    team_id,
    current_user
):

    try:

        shares = (
            db.query(Share)
            .options(
                joinedload(Share.password),
                joinedload(Share.sender),
            )
            .filter(
                Share.team_id
                == team_id
            )
            .order_by(
                Share.id.desc()
            )
            .all()
        )

        result = []

        from security.encryption import VaultEncryption
        from security.key_manager import KeyManager

        GLOBAL_KEY = (
            KeyManager.derive_key(
                "FIXED_KEY_123",
                "FIXED_SALT_123"
            )
        )

        for share in shares:

            password = share.password

            if not password:
                continue

            try:

                decrypted_password = (
                    VaultEncryption.decrypt_data(
                        password.encrypted_password,
                        password.encryption_nonce,
                        GLOBAL_KEY
                    )
                )

            except Exception:

                decrypted_password = "Cannot decrypt"

            # ------------------------------------------------
            # EDIT permission
            # ------------------------------------------------

            can_edit = False

            if is_admin(current_user):

                can_edit = True

            elif share.permission == "EDIT":

                team_member = (
                    db.query(TeamMember)
                    .filter(
                        TeamMember.team_id
                        == team_id,
                        TeamMember.user_id
                        == get_user_id(
                            current_user
                        ),
                    )
                    .first()
                )

                if team_member:
                    can_edit = True

            result.append({

                "share_id":
                    share.id,

                "password_id":
                    password.id,

                "title":
                    password.title,

                "username":
                    password.username,

                "password":
                    decrypted_password,

                "url":
                    password.url,

                "category":
                    password.category,

                "shared_from":
                    (
                        share.sender.name
                        if share.sender
                        else "Unknown"
                    ),

                "permission":
                    share.permission,

                "can_edit":
                    can_edit,
            })

        return result

    except Exception as exc:

        print(
            "ERROR getting team shared passwords:",
            exc
        )

        return []


# ============================================================
# GET DIRECT SHARED PASSWORDS
# ============================================================

def get_shared_passwords_for_user(
    db,
    user
):

    try:

        user_id = get_user_id(user)

        if not user_id:
            return []

        shares = (
            db.query(Share)
            .options(
                joinedload(Share.password),
                joinedload(Share.sender),
            )
            .filter(
                Share.receiver_id
                == user_id,
                Share.team_id.is_(None),
            )
            .order_by(
                Share.id.desc()
            )
            .all()
        )

        result = []

        from security.encryption import VaultEncryption
        from security.key_manager import KeyManager

        GLOBAL_KEY = (
            KeyManager.derive_key(
                "FIXED_KEY_123",
                "FIXED_SALT_123"
            )
        )

        for share in shares:

            password = share.password

            if not password:
                continue

            try:

                decrypted_password = (
                    VaultEncryption.decrypt_data(
                        password.encrypted_password,
                        password.encryption_nonce,
                        GLOBAL_KEY
                    )
                )

            except Exception:

                decrypted_password = "Cannot decrypt"

            can_edit = (
                share.sender_id == user_id
                or is_admin(user)
                or share.permission == "EDIT"
            )

            result.append({

                "share_id":
                    share.id,

                "password_id":
                    password.id,

                "title":
                    password.title,

                "username":
                    password.username,

                "password":
                    decrypted_password,

                "shared_from":
                    (
                        share.sender.name
                        if share.sender
                        else "Unknown"
                    ),

                "permission":
                    share.permission,

                "sender_id":
                    share.sender_id,

                "can_edit":
                    can_edit,
            })

        return result

    except Exception as exc:

        print(
            "ERROR fetching direct shared passwords:",
            exc
        )

        return []


# ============================================================
# GET SENT PASSWORDS
# ============================================================

def get_sent_passwords_for_user(
    db,
    user
):

    try:

        user_id = get_user_id(user)

        if not user_id:
            return []

        shares = (
            db.query(Share)
            .options(
                joinedload(Share.password),
                joinedload(Share.receiver),
                joinedload(Share.team),
            )
            .filter(
                Share.sender_id
                == user_id
            )
            .order_by(
                Share.id.desc()
            )
            .all()
        )

        result = []

        from security.encryption import VaultEncryption
        from security.key_manager import KeyManager

        GLOBAL_KEY = (
            KeyManager.derive_key(
                "FIXED_KEY_123",
                "FIXED_SALT_123"
            )
        )

        for share in shares:

            password = share.password

            if not password:
                continue

            try:

                decrypted_password = (
                    VaultEncryption.decrypt_data(
                        password.encrypted_password,
                        password.encryption_nonce,
                        GLOBAL_KEY
                    )
                )

            except Exception:

                decrypted_password = "Cannot decrypt"

            can_edit = True

            if share.team_id:

                shared_with = (
                    f"Team: {share.team.team_name}"
                    if share.team
                    else "Team"
                )

            else:

                shared_with = (
                    share.receiver.name
                    if share.receiver
                    else "Unknown"
                )

            result.append({

                "share_id":
                    share.id,

                "password_id":
                    password.id,

                "title":
                    password.title,

                "username":
                    password.username,

                "password":
                    decrypted_password,

                "shared_with":
                    shared_with,

                "permission":
                    share.permission,

                "can_edit":
                    can_edit,
            })

        return result

    except Exception as exc:

        print(
            "ERROR fetching sent passwords:",
            exc
        )

        return []


# ============================================================
# REMOVE SHARE
# ============================================================

def remove_share(
    db,
    user,
    share_id
):

    try:

        share = (
            db.query(Share)
            .filter(
                Share.id == share_id
            )
            .first()
        )

        if not share:
            return (
                False,
                "Share not found."
            )

        current_user_id = get_user_id(user)

        if (
            share.sender_id
            != current_user_id
            and not is_admin(user)
        ):
            return (
                False,
                "Only the person who shared this password (or Admin) can remove it."
            )

        db.delete(share)

        db.commit()

        return (
            True,
            "Share removed successfully."
        )

    except Exception as exc:

        db.rollback()

        return (
            False,
            str(exc)
        )