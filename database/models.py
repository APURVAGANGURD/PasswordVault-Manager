# database/models.py

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    LargeBinary,
    Text,
)

from sqlalchemy.orm import relationship

from database.connection import Base


# ============================================================
# USER
# ============================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    account_type = Column(
        Enum("PERSONAL", "ORGANIZATION"),
        nullable=False,
        default="PERSONAL",
    )

    role = Column(
        Enum("PERSONAL_USER", "OWNER", "ADMIN", "MANAGER", "USER"),
        nullable=False,
        default="PERSONAL_USER",
    )

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    )

    mfa_enabled = Column(Boolean, nullable=False, default=False)
    mfa_secret = Column(String(255), nullable=True)

    email_verified = Column(Boolean, nullable=False, default=False)

    status = Column(
        Enum("ACTIVE", "DISABLED"),
        nullable=False,
        default="ACTIVE",
    )

    failed_login_attempts = Column(Integer, nullable=False, default=0)
    locked_until = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # ---------------- Relationships ----------------
    organization = relationship(
        "Organization",
        back_populates="users",
        foreign_keys=[organization_id],
    )

    owned_organizations = relationship(
        "Organization",
        back_populates="owner",
        foreign_keys="Organization.owner_id",
    )

    vaults = relationship(
        "Vault",
        back_populates="owner",
        foreign_keys="Vault.owner_id",
    )

    team_memberships = relationship(
        "TeamMember",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    sent_shares = relationship(
        "Share",
        foreign_keys="Share.sender_id",
        back_populates="sender",
    )

    received_shares = relationship(
        "Share",
        foreign_keys="Share.receiver_id",
        back_populates="receiver",
    )

    audit_logs = relationship("AuditLog", back_populates="user")

    reset_tokens = relationship(
        "ResetToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    verification_tokens = relationship(
        "VerificationToken",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    notification_preferences = relationship(
        "UserPreference",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


# ============================================================
# ORGANIZATION
# ============================================================

class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)

    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    owner = relationship(
        "User",
        back_populates="owned_organizations",
        foreign_keys=[owner_id],
    )

    users = relationship(
        "User",
        back_populates="organization",
        foreign_keys="User.organization_id",
    )

    departments = relationship(
        "Department",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    teams = relationship(
        "Team",
        back_populates="organization",
        cascade="all, delete-orphan",
    )

    vaults = relationship("Vault", back_populates="organization")

    audit_logs = relationship("AuditLog", back_populates="organization")


# ============================================================
# DEPARTMENT
# ============================================================

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, autoincrement=True)

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="departments")
    teams = relationship("Team", back_populates="department")


# ============================================================
# TEAM
# ============================================================

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, autoincrement=True)

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    department_id = Column(
        Integer,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
    )

    team_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="teams")
    department = relationship("Department", back_populates="teams")
    creator = relationship("User", foreign_keys=[created_by])

    members = relationship(
        "TeamMember",
        back_populates="team",
        cascade="all, delete-orphan",
    )

    vaults = relationship("Vault", back_populates="team")


# ============================================================
# TEAM MEMBER
# ============================================================

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, autoincrement=True)

    team_id = Column(
        Integer,
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=False,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    email = Column(String(255), nullable=True)

    role = Column(
        Enum("MANAGER", "USER", "EMPLOYEE"),
        nullable=False,
        default="EMPLOYEE",
    )

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    joined_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")


# ============================================================
# VAULT
# ============================================================

class Vault(Base):
    __tablename__ = "vaults"

    id = Column(Integer, primary_key=True, autoincrement=True)

    owner_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )

    team_id = Column(
        Integer,
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=True,
    )

    name = Column(String(255), nullable=False)

    vault_type = Column(
        Enum("PERSONAL", "TEAM", "SHARED"),
        nullable=False,
        default="PERSONAL",
    )

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    owner = relationship(
        "User",
        back_populates="vaults",
        foreign_keys=[owner_id],
    )

    organization = relationship("Organization", back_populates="vaults")
    team = relationship("Team", back_populates="vaults")

    passwords = relationship(
        "Password",
        back_populates="vault",
        cascade="all, delete-orphan",
    )


# ============================================================
# PASSWORD
# ============================================================

class Password(Base):
    __tablename__ = "passwords"

    id = Column(Integer, primary_key=True, autoincrement=True)

    vault_id = Column(
        Integer,
        ForeignKey("vaults.id", ondelete="CASCADE"),
        nullable=False,
    )

    title = Column(String(255), nullable=False)
    username = Column(String(255), nullable=True)

    encrypted_password = Column(LargeBinary, nullable=False)
    encryption_nonce = Column(LargeBinary, nullable=False)

    url = Column(String(255), nullable=True)
    encrypted_notes = Column(LargeBinary, nullable=True)
    category = Column(String(255), nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    favorite = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    vault = relationship("Vault", back_populates="passwords")
    shares = relationship(
        "Share",
        back_populates="password",
        cascade="all, delete-orphan",
    )


# ============================================================
# SHARE
# ============================================================

class Share(Base):
    __tablename__ = "shares"

    id = Column(Integer, primary_key=True, autoincrement=True)

    password_id = Column(
        Integer,
        ForeignKey("passwords.id", ondelete="CASCADE"),
        nullable=False,
    )

    sender_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    receiver_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )

    team_id = Column(
        Integer,
        ForeignKey("teams.id", ondelete="CASCADE"),
        nullable=True,
    )

    permission = Column(
        Enum("VIEW", "EDIT"),
        nullable=False,
        default="VIEW",
    )

    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    password = relationship("Password", back_populates="shares")

    sender = relationship(
        "User",
        foreign_keys=[sender_id],
        back_populates="sent_shares",
    )

    receiver = relationship(
        "User",
        foreign_keys=[receiver_id],
        back_populates="received_shares",
    )

    team = relationship("Team")


# ============================================================
# AUDIT LOG  — full activity record with IP / device / browser
# ============================================================

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    organization_id = Column(
        Integer,
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
    )

    # What happened
    action = Column(String(255), nullable=False)

    # What it happened to
    target_type = Column(String(255), nullable=True)
    target_id = Column(Integer, nullable=True)

    # When
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Where from
    ip_address = Column(String(255), nullable=True)
    device = Column(String(255), nullable=True)
    browser = Column(String(255), nullable=True)

    # Extra metadata (JSON-ish string for flexibility)
    details = Column(Text, nullable=True)

    # ---------------- Relationships ----------------
    user = relationship("User", back_populates="audit_logs")
    organization = relationship("Organization", back_populates="audit_logs")


# ============================================================
# RESET TOKEN
# ============================================================

class ResetToken(Base):
    __tablename__ = "reset_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="reset_tokens")


# ============================================================
# VERIFICATION TOKEN
# ============================================================

class VerificationToken(Base):
    __tablename__ = "verification_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    token_hash = Column(String(255), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="verification_tokens")


# ============================================================
# USER PREFERENCES
# ============================================================

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    password_shared_with_me = Column(Boolean, nullable=False, default=True)
    password_shared_by_me = Column(Boolean, nullable=False, default=True)
    password_health_alerts = Column(Boolean, nullable=False, default=True)
    security_alerts = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    user = relationship("User", back_populates="notification_preferences")