import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import get_db
from database import models


def is_admin(user):
    return str(user.get("role", "")).upper() in ["OWNER", "ADMIN"]


def is_manager(user):
    return str(user.get("role", "")).upper() in ["OWNER", "ADMIN", "MANAGER"]


def get_user_organization(db, user):
    """Return the Organization for this user (owner or member)."""
    user_id = user.get("id") if isinstance(user, dict) else getattr(user, "id", None)
    if not user_id:
        return None

    # Owner?
    org = db.query(models.Organization).filter(
        models.Organization.owner_id == user_id
    ).first()
    if org:
        return org

    # Team member?
    org = (
        db.query(models.Organization)
        .join(models.Team, models.Team.organization_id == models.Organization.id)
        .join(models.TeamMember, models.TeamMember.team_id == models.Team.id)
        .filter(models.TeamMember.user_id == user_id)
        .first()
    )
    return org


def get_departments(db, organization_id):
    return db.query(models.Department).filter(
        models.Department.organization_id == organization_id
    ).all()


def get_user_teams(db, user, organization_id):
    if is_admin(user):
        return db.query(models.Team).filter(
            models.Team.organization_id == organization_id
        ).all()

    return (
        db.query(models.Team)
        .join(models.TeamMember, models.TeamMember.team_id == models.Team.id)
        .filter(
            models.Team.organization_id == organization_id,
            models.TeamMember.user_id == user["id"],
        )
        .all()
    )


def create_team(db, user, team_name, department_id, description):
    if not is_admin(user):
        return False, "You do not have permission to perform this action."

    org = get_user_organization(db, user)
    if not org:
        return False, "You are not associated with an organization."

    team_name = (team_name or "").strip()
    if not team_name:
        return False, "Team name is required."

    existing = db.query(models.Team).filter(
        models.Team.organization_id == org.id,
        models.Team.team_name == team_name,
    ).first()
    if existing:
        return False, "A team with this name already exists."

    try:
        new_team = models.Team(
            team_name=team_name,
            organization_id=org.id,
            department_id=department_id,
            description=description,
            created_by=user["id"],
        )
        db.add(new_team)
        db.commit()
        db.refresh(new_team)
        return True, new_team
    except Exception as exc:
        db.rollback()
        return False, f"Unable to create team: {exc}"


def add_team_member(db, user, team_id, email, role):
    if not is_manager(user):
        return False, "You do not have permission to perform this action."

    email = (email or "").strip().lower()
    if not email:
        return False, "Member email is required."

    target_user = db.query(models.User).filter(
        models.User.email == email
    ).first()
    if not target_user:
        return False, "No user found with this email address."

    existing = db.query(models.TeamMember).filter(
        models.TeamMember.team_id == team_id,
        models.TeamMember.user_id == target_user.id,
    ).first()
    if existing:
        return False, "This user is already a member of this team."

    try:
        role = (role or "EMPLOYEE").upper()
        if role == "USER":
            role = "EMPLOYEE"

        new_member = models.TeamMember(
            team_id=team_id,
            user_id=target_user.id,
            email=target_user.email,
            role=role,
        )
        db.add(new_member)
        db.commit()
        return True, "Member added successfully."
    except Exception as exc:
        db.rollback()
        return False, f"Unable to add member: {exc}"


def remove_team_member(db, user, team_id, member_id):
    if not is_manager(user):
        return False, "You do not have permission to perform this action."
    try:
        member = db.query(models.TeamMember).filter(
            models.TeamMember.id == member_id,
            models.TeamMember.team_id == team_id,
        ).first()
        if member:
            db.delete(member)
            db.commit()
            return True, "Member removed successfully."
        return False, "Member not found."
    except Exception as exc:
        db.rollback()
        return False, f"Unable to remove member: {exc}"


def update_member_role(db, user, team_id, member_id, new_role):
    if not is_admin(user):
        return False, "You do not have permission to perform this action."
    try:
        member = db.query(models.TeamMember).filter(
            models.TeamMember.id == member_id,
            models.TeamMember.team_id == team_id,
        ).first()
        if member:
            member.role = (new_role or "EMPLOYEE").upper()
            db.commit()
            return True, "Role updated successfully."
        return False, "Member not found."
    except Exception as exc:
        db.rollback()
        return False, f"Unable to update role: {exc}"


def delete_team(db, user, team_id):
    """Delete a team plus its members and shares."""
    if not is_admin(user):
        return False, "You do not have permission to perform this action."
    try:
        db.query(models.TeamMember).filter(
            models.TeamMember.team_id == team_id
        ).delete(synchronize_session=False)

        db.query(models.Share).filter(
            models.Share.team_id == team_id
        ).delete(synchronize_session=False)

        team = db.query(models.Team).filter(
            models.Team.id == team_id
        ).first()
        if team:
            db.delete(team)
            db.commit()
            return True, "Team deleted successfully."
        return False, "Team not found."
    except Exception as exc:
        db.rollback()
        return False, f"Unable to delete team: {exc}"