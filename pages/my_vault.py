import streamlit as st
import sys
import os
import html
from datetime import datetime

# ============================================================
# PROJECT ROOT
# ============================================================

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

# ============================================================
# PROJECT IMPORTS
# ============================================================

from database.connection import get_db
from database import models
from security.password_strength import estimate_strength

from utils.vault_crypto import (
    encrypt_text,
    decrypt_text,
    encrypt_notes,
    decrypt_notes,
)

try:
    from utils.audit_logger import create_audit_log
except ImportError:
    create_audit_log = None


from utils.theme import render_html, inject_cyber_theme

# ============================================================
# CSS
# ============================================================

def load_css():
    inject_cyber_theme()
    render_html(
        """
        <style>
        /* Typography */
        .vault-title {
            font-size: 26px;
            font-weight: 800;
            color: #f8fafc;
            letter-spacing: -0.4px;
            margin-bottom: 4px;
        }
        .vault-subtitle {
            font-size: 13.5px;
            color: #94a3b8;
            margin-bottom: 20px;
        }

        /* Info bar */
        .vault-info {
            background: rgba(13, 22, 42, 0.7);
            border: 1px solid rgba(56, 189, 248, 0.18);
            border-radius: 12px;
            padding: 14px 18px;
            margin: 14px 0 18px 0;
            color: #94a3b8;
            font-size: 13px;
        }

        /* Password cards */
        .password-card {
            background: rgba(13, 22, 42, 0.75);
            border: 1px solid rgba(56, 189, 248, 0.16);
            border-radius: 10px;
            padding: 12px 16px;
            margin-bottom: 8px;
            min-height: 48px;
            display: flex;
            align-items: center;
            transition: all 0.2s ease;
        }
        .password-card:hover {
            border-color: rgba(56, 189, 248, 0.4);
            background: rgba(20, 33, 62, 0.85);
        }
        .password-title {
            color: #f8fafc;
            font-size: 13.5px;
            font-weight: 600;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        .password-value {
            color: #cbd5e1;
            font-size: 13px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            font-family: 'JetBrains Mono', monospace;
        }
        .password-url {
            color: #38bdf8;
            font-size: 13px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }

        .table-header {
            color: #94a3b8;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.6px;
            padding: 0 5px 8px 5px;
        }

        /* Strength badges */
        .strength-strong {
            display: inline-block;
            background: rgba(16, 185, 129, 0.14);
            color: #34d399;
            border: 1px solid rgba(16, 185, 129, 0.35);
            border-radius: 20px;
            padding: 4px 10px;
            font-size: 10.5px;
            font-weight: 700;
        }
        .strength-medium {
            display: inline-block;
            background: rgba(245, 158, 11, 0.14);
            color: #fbbf24;
            border: 1px solid rgba(245, 158, 11, 0.35);
            border-radius: 20px;
            padding: 4px 10px;
            font-size: 10.5px;
            font-weight: 700;
        }
        .strength-weak {
            display: inline-block;
            background: rgba(244, 63, 94, 0.14);
            color: #fb7185;
            border: 1px solid rgba(244, 63, 94, 0.35);
            border-radius: 20px;
            padding: 4px 10px;
            font-size: 10.5px;
            font-weight: 700;
        }
        .strength-very-weak {
            display: inline-block;
            background: rgba(244, 63, 94, 0.2);
            color: #f43f5e;
            border: 1px solid rgba(244, 63, 94, 0.5);
            border-radius: 20px;
            padding: 4px 10px;
            font-size: 10.5px;
            font-weight: 700;
        }

        /* Empty state */
        .empty-card {
            background: rgba(13, 22, 42, 0.5);
            border: 1px dashed rgba(56, 189, 248, 0.22);
            border-radius: 12px;
            padding: 45px 20px;
            text-align: center;
            margin-top: 15px;
        }
        .empty-title {
            color: #f8fafc;
            font-size: 18px;
            font-weight: 700;
        }
        .empty-text {
            color: #94a3b8;
            font-size: 13px;
            margin-top: 6px;
        }

        /* Warnings */
        .delete-warning {
            background: rgba(244, 63, 94, 0.14);
            border: 1px solid rgba(244, 63, 94, 0.4);
            border-radius: 10px;
            padding: 14px 18px;
            color: #fb7185;
            font-size: 13.5px;
            margin: 12px 0;
        }
        .decrypt-warning {
            background: rgba(245, 158, 11, 0.14);
            border: 1px solid rgba(245, 158, 11, 0.4);
            border-radius: 10px;
            padding: 14px 18px;
            color: #fbbf24;
            font-size: 13.5px;
            margin: 14px 0;
        }
        </style>
        """
    )
# ============================================================
# USER HELPERS
# ============================================================

def get_user_id(user):

    if isinstance(user, dict):
        return user.get("id")

    return getattr(user, "id", None)


# ============================================================
# PERSONAL VAULT
# ============================================================

def get_personal_vault(db, user):

    user_id = get_user_id(user)

    if user_id is None:
        return None

    vault = (
        db.query(models.Vault)
        .filter(
            models.Vault.owner_id == user_id,
            models.Vault.vault_type == "PERSONAL"
        )
        .first()
    )

    if vault:
        return vault

    vault = models.Vault(
        owner_id=user_id,
        organization_id=None,
        team_id=None,
        name="Personal Vault",
        vault_type="PERSONAL"
    )

    db.add(vault)
    db.commit()
    db.refresh(vault)

    return vault


# ============================================================
# PASSWORD STRENGTH
# ============================================================

def get_strength_class(label):

    label = str(label).lower().strip()

    if "very weak" in label:
        return "strength-very-weak"

    if "weak" in label:
        return "strength-weak"

    if (
        "medium" in label
        or "moderate" in label
        or "average" in label
    ):
        return "strength-medium"

    return "strength-strong"


def strength_badge(label):

    css_class = get_strength_class(label)

    safe_label = html.escape(str(label).upper())

    return (
        f'<span class="{css_class}">'
        f'{safe_label}'
        f'</span>'
    )


# ============================================================
# PASSWORD DECRYPTION
# ============================================================

def decrypt_password(record):
    """
    Decrypt password using centralized key management.
    Handles both current and legacy keys automatically.
    """

    if not record:
        return None

    if not record.encrypted_password:
        return None

    if not record.encryption_nonce:
        return None

    value = decrypt_text(
        record.encrypted_password,
        record.encryption_nonce
    )

    if not value:
        return None

    return value


# ============================================================
# PASSWORD ENCRYPTION
# ============================================================

def encrypt_password(password):
    """
    Encrypt password with the current active key.
    """

    if not password:
        raise ValueError("Password cannot be empty.")

    encrypted_password, nonce = encrypt_text(password)

    return encrypted_password, nonce


# ============================================================
# NOTES ENCRYPTION / DECRYPTION
# ============================================================

def encrypt_password_notes(notes):
    """
    Returns bytes in the format b"nonce_hex:ciphertext_hex"
    """

    if not notes:
        return None

    enc_hex, nonce_hex = encrypt_notes(notes)

    if not enc_hex or not nonce_hex:
        return None

    return f"{nonce_hex}:{enc_hex}".encode("utf-8")


def decrypt_password_notes(encrypted_notes):

    if not encrypted_notes:
        return ""

    try:

        if isinstance(encrypted_notes, bytes):
            value = encrypted_notes.decode("utf-8")
        else:
            value = str(encrypted_notes)

        if ":" not in value:
            return ""

        nonce_hex, encrypted_hex = value.split(":", 1)

        return decrypt_notes(encrypted_hex, nonce_hex)

    except Exception:
        return ""


# ============================================================
# AUDIT
# ============================================================

def audit(user_id, action, target, target_type="PASSWORD", target_id=None):

    if create_audit_log is None:
        return

    try:
        create_audit_log(
            user_id=user_id,
            action=action,
            target=target,
            target_type=target_type,
            target_id=target_id,
        )
    except Exception:
        pass


# ============================================================
# EDIT PASSWORD
# ============================================================

def show_edit_form(db, record, user):

    render_html(
        '<div class="edit-card-title">'
        '✏ Edit Password'
        '</div>'
    )

    # --------------------------------------------------------
    # DECRYPT CURRENT PASSWORD
    # --------------------------------------------------------

    current_password = decrypt_password(record)

    if current_password is None:

        render_html(
            """
            <div class="decrypt-warning">
                <b>Unable to decrypt this password.</b><br><br>
                This record was encrypted with a key that is not
                currently available. Please make sure the same
                VAULT_MASTER_KEY (or the original FIXED_KEY_123)
                is configured.
            </div>
            """
        )

        if st.button(
            "← Back to My Vault",
            use_container_width=True,
            key="edit_back_decrypt_error",
        ):
            st.session_state.pop("editing_password_id", None)
            st.rerun()

        return

    # --------------------------------------------------------
    # DECRYPT NOTES
    # --------------------------------------------------------

    current_notes = decrypt_password_notes(record.encrypted_notes)

    # --------------------------------------------------------
    # FORM
    # --------------------------------------------------------

    with st.form(f"edit_password_{record.id}"):

        col1, col2 = st.columns(2)

        with col1:
            title = st.text_input(
                "Title *",
                value=record.title or ""
            )

        with col2:
            username = st.text_input(
                "Username *",
                value=record.username or ""
            )

        password = st.text_input(
            "Password *",
            value=current_password,
            type="password"
        )

        url = st.text_input(
            "Website URL",
            value=record.url or ""
        )

        col3, col4 = st.columns(2)

        categories = [
            "Work",
            "Social",
            "Development",
            "Cloud",
            "Finance",
            "Database",
            "Entertainment",
            "Other"
        ]

        current_category = (
            record.category
            if record.category in categories
            else "Other"
        )

        with col3:
            category = st.selectbox(
                "Category",
                categories,
                index=categories.index(current_category)
            )

        with col4:
            expiry_enabled = st.checkbox(
                "Set expiry date",
                value=record.expiry_date is not None
            )

            expiry = st.date_input(
                "Expiry Date",
                value=(
                    record.expiry_date.date()
                    if record.expiry_date
                    else datetime.now().date()
                ),
                disabled=not expiry_enabled
            )

        notes = st.text_area(
            "Notes",
            value=current_notes
        )

        save_col, cancel_col = st.columns(2)

        with save_col:
            save = st.form_submit_button(
                "💾 Save Changes",
                type="primary",
                use_container_width=True
            )

        with cancel_col:
            cancel = st.form_submit_button(
                "Cancel",
                use_container_width=True
            )

        # ----------------------------------------------------
        # CANCEL
        # ----------------------------------------------------

        if cancel:
            st.session_state.pop("editing_password_id", None)
            st.rerun()

        # ----------------------------------------------------
        # SAVE
        # ----------------------------------------------------

        if save:

            if not title.strip():
                st.error("Title is required.")
                return

            if not username.strip():
                st.error("Username is required.")
                return

            if not password:
                st.error("Password is required.")
                return

            try:

                encrypted_password, nonce = encrypt_password(password)

                encrypted_notes = encrypt_password_notes(notes.strip())

                record.title = title.strip()
                record.username = username.strip()
                record.encrypted_password = encrypted_password
                record.encryption_nonce = nonce
                record.url = url.strip() if url.strip() else None
                record.category = category
                record.expiry_date = expiry if expiry_enabled else None
                record.encrypted_notes = encrypted_notes
                record.updated_at = datetime.utcnow()

                db.commit()

                audit(
                    user_id=get_user_id(user),
                    action="PASSWORD_UPDATED",
                    target=f"Updated password: {record.title or 'Untitled'}",
                    target_type="PASSWORD",
                    target_id=record.id,
                )

                st.session_state.pop("editing_password_id", None)
                st.success("Password updated successfully.")
                st.rerun()

            except Exception as e:
                db.rollback()
                st.error("Could not update password.")
                st.exception(e)


# ============================================================
# VIEW PASSWORD
# ============================================================

def show_view_password(db, record, user):

    """
    Secure authenticated password-view screen.

    Password is:
        - encrypted in database
        - decrypted only in memory
        - masked by default
        - revealed only when user clicks 👁
        - never written to audit logs

    Audit events:
        PASSWORD_VIEWED
        PASSWORD_REVEALED
        PASSWORD_MASKED
    """

    # --------------------------------------------------------
    # DECRYPT PASSWORD
    # --------------------------------------------------------

    password = decrypt_password(record)

    if password is None:

        st.error(
            "Unable to decrypt this password."
        )

        st.info(
            "The password is stored encrypted, but it could "
            "not be decrypted with the current encryption key."
        )

        if st.button(
            "← Back to My Vault",
            use_container_width=True,
            key="back_decrypt_error",
        ):
            st.session_state.pop(
                "current_view_id",
                None
            )
            st.rerun()

        return

    # --------------------------------------------------------
    # SESSION KEY
    # --------------------------------------------------------

    visibility_key = f"password_visible_{record.id}"

    if visibility_key not in st.session_state:
        st.session_state[visibility_key] = False

    password_visible = bool(
        st.session_state[visibility_key]
    )

    # --------------------------------------------------------
    # AUDIT - PASSWORD_VIEWED (once per view session)
    # --------------------------------------------------------

    viewed_key = f"password_viewed_logged_{record.id}"

    if not st.session_state.get(viewed_key):

        audit(
            user_id=get_user_id(user),
            action="PASSWORD_VIEWED",
            target=(
                f"Viewed password: "
                f"{record.title or 'Untitled'}"
            ),
            target_type="PASSWORD",
            target_id=record.id,
        )

        st.session_state[viewed_key] = True

    # --------------------------------------------------------
    # PAGE HEADER
    # --------------------------------------------------------

    render_html(
        """
        <div class="edit-card-title">
            🔐 View Password
        </div>
        """
    )

    render_html(
        """
        <div style="
            color:#7b8698;
            font-size:13px;
            margin-bottom:20px;
        ">
            View your saved password securely.
        </div>
        """
    )

    # --------------------------------------------------------
    # TWO COLUMN LAYOUT
    # --------------------------------------------------------

    left, right = st.columns(
        [2.1, 1],
        gap="large"
    )

    # ========================================================
    # LEFT - PASSWORD INFORMATION
    # ========================================================

    with left:

        render_html(
            """
            <div style="
                background: rgba(13, 22, 42, 0.75);
                border: 1px solid rgba(56, 189, 248, 0.16);
                border-radius: 12px;
                padding: 20px;
            ">
            """
        )

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        render_html(
            """
            <div style="
                font-size:11px;
                color:#8993a4;
                font-weight:700;
                margin-bottom:5px;
            ">
                Title
            </div>
            """
        )

        render_html(
            f"""
            <div style="
                font-size:14px;
                color:#f8fafc;
                font-weight:600;
                margin-bottom:20px;
            ">
                {html.escape(record.title or "-")}
            </div>
            """
        )

        # ----------------------------------------------------
        # USERNAME
        # ----------------------------------------------------

        render_html(
            """
            <div style="
                font-size:11px;
                color:#8993a4;
                font-weight:700;
                margin-bottom:5px;
            ">
                Username
            </div>
            """
        )

        render_html(
            f"""
            <div style="
                font-size:14px;
                color:#f8fafc;
                margin-bottom:20px;
            ">
                {html.escape(record.username or "-")}
            </div>
            """
        )

        # ----------------------------------------------------
        # PASSWORD
        # ----------------------------------------------------

        render_html(
            """
            <div style="
                font-size:11px;
                color:#8993a4;
                font-weight:700;
                margin-bottom:5px;
            ">
                Password
            </div>
            """
        )

        if password_visible:
            display_password = html.escape(password)
        else:
            display_password = "••••••••••••••••"

        pw_col, eye_col = st.columns(
            [8, 1],
            gap="small"
        )

        with pw_col:

            render_html(
                f"""
                <div style="
                    min-height:44px;
                    border:1px solid rgba(56, 189, 248, 0.25);
                    border-radius:8px;
                    background:rgba(13, 22, 42, 0.85);
                    padding:11px 13px;
                    color:#38bdf8;
                    font-size:13px;
                    font-family:monospace;
                    overflow-x:auto;
                    white-space:nowrap;
                ">
                    {display_password}
                </div>
                """
            )

        with eye_col:

            if st.button(
                "🙈" if password_visible else "👁",
                key=f"password_eye_{record.id}",
                help=(
                    "Hide password"
                    if password_visible
                    else "Show password"
                ),
                use_container_width=True,
            ):

                # --------------------------------------------
                # REVEAL
                # --------------------------------------------

                if not password_visible:

                    st.session_state[
                        visibility_key
                    ] = True

                    audit(
                        user_id=get_user_id(user),
                        action="PASSWORD_REVEALED",
                        target=(
                            f"Revealed password: "
                            f"{record.title or 'Untitled'}"
                        ),
                        target_type="PASSWORD",
                        target_id=record.id,
                    )

                # --------------------------------------------
                # HIDE
                # --------------------------------------------

                else:

                    st.session_state[
                        visibility_key
                    ] = False

                    audit(
                        user_id=get_user_id(user),
                        action="PASSWORD_MASKED",
                        target=(
                            f"Masked password: "
                            f"{record.title or 'Untitled'}"
                        ),
                        target_type="PASSWORD",
                        target_id=record.id,
                    )

                st.rerun()

        # ----------------------------------------------------
        # PASSWORD STRENGTH
        # ----------------------------------------------------

        try:
            strength = estimate_strength(password)
            strength_label = strength["label"]
        except Exception:
            strength_label = "ERROR"

        render_html(
            """
            <div style="
                font-size:11px;
                color:#8993a4;
                font-weight:700;
                margin-top:20px;
                margin-bottom:7px;
            ">
                Password Strength
            </div>
            """
        )

        if strength_label == "ERROR":
            render_html(
                """
                <span class="strength-weak">ERROR</span>
                """
            )
        else:
            strength_class = get_strength_class(strength_label)
            render_html(
                f"""
                <span class="{strength_class}">
                    {html.escape(str(strength_label).upper())}
                </span>
                """
            )

        # ----------------------------------------------------
        # WEBSITE
        # ----------------------------------------------------

        render_html(
            """
            <div style="
                font-size:11px;
                color:#8993a4;
                font-weight:700;
                margin-top:20px;
                margin-bottom:5px;
            ">
                Website URL
            </div>
            """
        )

        if record.url:

            safe_url = html.escape(
                record.url,
                quote=True
            )

            safe_url_text = html.escape(
                record.url
            )

            render_html(
                f"""
                <div style="
                    font-size:13px;
                    margin-bottom:20px;
                ">
                    <a href="{safe_url}"
                       target="_blank"
                       style="color:#38bdf8;">
                        {safe_url_text}
                    </a>
                </div>
                """
            )

        else:

            render_html(
                """
                <div style="
                    color:#7b8698;
                    margin-bottom:20px;
                ">
                    -
                </div>
                """
            )

        # ----------------------------------------------------
        # CATEGORY + EXPIRY
        # ----------------------------------------------------

        c1, c2 = st.columns(2)

        with c1:

            render_html(
                """
                <div style="
                    font-size:11px;
                    color:#8993a4;
                    font-weight:700;
                    margin-bottom:5px;
                ">
                    Category
                </div>
                """
            )

            st.write(
                record.category or "-"
            )

        with c2:

            render_html(
                """
                <div style="
                    font-size:11px;
                    color:#8993a4;
                    font-weight:700;
                    margin-bottom:5px;
                ">
                    Expiry Date
                </div>
                """
            )

            expiry = (
                record.expiry_date.strftime(
                    "%Y-%m-%d"
                )
                if record.expiry_date
                else "-"
            )

            st.write(expiry)

        # ----------------------------------------------------
        # NOTES
        # ----------------------------------------------------

        notes = decrypt_password_notes(
            record.encrypted_notes
        )

        if notes:

            render_html(
                """
                <div style="
                    font-size:11px;
                    color:#8993a4;
                    font-weight:700;
                    margin-top:20px;
                    margin-bottom:5px;
                ">
                    Notes
                </div>
                """
            )

            st.text_area(
                "Notes",
                value=notes,
                disabled=True,
                label_visibility="collapsed",
                key=f"view_notes_{record.id}",
            )

        render_html("</div>")

    # ========================================================
    # RIGHT - PASSWORD DETAILS
    # ========================================================

    with right:

        render_html(
            """
            <div style="
                background: rgba(13, 22, 42, 0.75);
                border: 1px solid rgba(56, 189, 248, 0.16);
                border-radius: 12px;
                padding: 20px;
            ">
                <div style="
                    font-size:16px;
                    font-weight:750;
                    color:#f8fafc;
                    margin-bottom:20px;
                ">
                    Password Details
                </div>
            """
        )

        # Created
        st.markdown("**Created At**")

        st.caption(
            record.created_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            if record.created_at
            else "-"
        )

        # Updated
        st.markdown("**Last Updated**")

        st.caption(
            record.updated_at.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            if record.updated_at
            else "-"
        )

        # Vault
        st.markdown("**Vault**")

        vault_name = "-"

        try:
            if record.vault:
                vault_name = (
                    record.vault.name
                    or "Personal Vault"
                )
        except Exception:
            vault_name = "Personal Vault"

        st.caption(vault_name)

        # Password ID
        st.markdown("**Password ID**")

        st.caption(str(record.id))

        # Favorite
        st.markdown("**Favorite**")

        st.caption(
            "⭐ Yes"
            if record.favorite
            else "No"
        )

        render_html("</div>")

    # ========================================================
    # BACK BUTTON
    # ========================================================

    st.write("")

    if st.button(
        "← Back to My Vault",
        use_container_width=True,
        key=f"back_view_{record.id}",
    ):

        st.session_state.pop(
            "current_view_id",
            None
        )

        st.session_state.pop(
            visibility_key,
            None
        )

        # Clear viewed flag so re-opening logs PASSWORD_VIEWED again
        st.session_state.pop(
            f"password_viewed_logged_{record.id}",
            None
        )

        st.rerun()


# ============================================================
# DELETE PASSWORD
# ============================================================

def delete_password(db, record, user):

    password_id = record.id
    password_title = record.title or "Password"

    try:

        db.delete(record)
        db.commit()

        audit(
            user_id=get_user_id(user),
            action="PASSWORD_DELETED",
            target=f"Deleted password: {password_title}",
            target_type="PASSWORD",
            target_id=password_id,
        )

        st.session_state.pop("delete_password_id", None)
        st.success(f"{password_title} deleted.")
        st.rerun()

    except Exception as e:

        db.rollback()
        st.error("Could not delete password.")
        st.exception(e)


# ============================================================
# MAIN PAGE
# ============================================================

def show(user):

    load_css()

    render_html(
        '<div class="vault-title">'
        'My Vault'
        '</div>'
    )

    render_html(
        '<div class="vault-subtitle">'
        'Manage your personal passwords securely'
        '</div>'
    )

    user_id = get_user_id(user)

    if user_id is None:
        st.error("Your session is invalid. Please log in again.")
        return

    db = next(get_db())

    try:

        current_user = (
            db.query(models.User)
            .filter(models.User.id == user_id)
            .first()
        )

        if not current_user:
            st.error("User account could not be found.")
            return

        vault = get_personal_vault(db, current_user)

        if vault is None:
            st.error("Unable to load your personal vault.")
            return

        # ====================================================
        # VIEW PASSWORD
        # ====================================================

        view_id = st.session_state.get("current_view_id")

        if view_id:

            view_record = (
                db.query(models.Password)
                .filter(
                    models.Password.id == view_id,
                    models.Password.vault_id == vault.id
                )
                .first()
            )

            if not view_record:
                st.error("Password record not found.")
                st.session_state.pop("current_view_id", None)
                return

            show_view_password(db, view_record, current_user)
            return

        # ====================================================
        # TOP CONTROLS
        # ====================================================

        col_search, col_category, col_add = st.columns([2.6, 1.3, 1])

        with col_search:
            search = st.text_input(
                "Search",
                placeholder="🔍 Search passwords...",
                label_visibility="collapsed"
            )

        with col_category:

            categories = [
                "All Categories",
                "Work",
                "Social",
                "Development",
                "Cloud",
                "Finance",
                "Database",
                "Entertainment",
                "Other"
            ]

            selected_category = st.selectbox(
                "Category",
                categories,
                label_visibility="collapsed"
            )

        with col_add:

            if st.button(
                "＋ Add Password",
                type="primary",
                use_container_width=True
            ):
                st.session_state["nav"] = "Add Password"
                st.rerun()

        # ====================================================
        # FETCH PASSWORDS
        # ====================================================

        records = (
            db.query(models.Password)
            .filter(models.Password.vault_id == vault.id)
            .order_by(models.Password.updated_at.desc())
            .all()
        )

        # ====================================================
        # FILTER
        # ====================================================

        filtered_records = []

        for record in records:

            if search:
                search_text = (
                    f"{record.title or ''} "
                    f"{record.username or ''} "
                    f"{record.url or ''} "
                    f"{record.category or ''}"
                ).lower()

                if search.lower() not in search_text:
                    continue

            if selected_category != "All Categories":
                if record.category != selected_category:
                    continue

            filtered_records.append(record)

        # ====================================================
        # INFO
        # ====================================================

        render_html(
            f"""
            <div class="vault-info">
                Showing <b>{len(filtered_records)}</b>
                of <b>{len(records)}</b> passwords
            </div>
            """
        )

        # ====================================================
        # EMPTY
        # ====================================================

        if not filtered_records:

            render_html(
                """
                <div class="empty-card">
                    <div style="font-size:42px;">🔐</div>
                    <div class="empty-title">No passwords found</div>
                    <div class="empty-text">
                        Add your first password to your secure vault.
                    </div>
                </div>
                """
            )

            return

        # ====================================================
        # TABLE HEADER
        # ====================================================

        (h1, h2, h3, h4, h5, h6, h7) = st.columns(
            [1.4, 1.25, 1.5, 0.9, 0.9, 1.7, 1.7]
        )

        headers = [
            "Title",
            "Username",
            "URL",
            "Category",
            "Strength",
            "Expiry",
            "Actions"
        ]

        for col, label in zip(
            [h1, h2, h3, h4, h5, h6, h7],
            headers
        ):
            with col:
                render_html(
                    f'<div class="table-header">{label}</div>'
                )

        # ====================================================
        # PASSWORD ROWS
        # ====================================================

        for record in filtered_records:

            plain_password = decrypt_password(record)

            if plain_password is not None:
                try:
                    strength = estimate_strength(plain_password)
                    strength_label = strength["label"]
                except Exception:
                    strength_label = "ERROR"
            else:
                strength_label = "ERROR"

            title = html.escape(record.title or "Untitled")
            username = html.escape(record.username or "-")
            url = html.escape(record.url or "-")
            category = html.escape(record.category or "-")

            expiry = (
                record.expiry_date.strftime("%Y-%m-%d")
                if record.expiry_date
                else "-"
            )

            (c1, c2, c3, c4, c5, c6, c7) = st.columns(
                [1.4, 1.25, 1.5, 0.9, 0.9, 1.7, 1.7]
            )

            with c1:
                render_html(
                    f"""
                    <div class="password-card">
                        <div class="password-title">{title}</div>
                    </div>
                    """
                )

            with c2:
                render_html(
                    f"""
                    <div class="password-card">
                        <div class="password-value">{username}</div>
                    </div>
                    """
                )

            with c3:
                render_html(
                    f"""
                    <div class="password-card">
                        <div class="password-url">{url}</div>
                    </div>
                    """
                )

            with c4:
                render_html(
                    f"""
                    <div class="password-card">
                        <div class="password-value">{category}</div>
                    </div>
                    """
                )

            with c5:
                if strength_label == "ERROR":
                    render_html(
                        """
                        <div class="password-card">
                            <span class="strength-weak">ERROR</span>
                        </div>
                        """
                    )
                else:
                    badge = strength_badge(strength_label)
                    render_html(
                        f"""
                        <div class="password-card">{badge}</div>
                        """
                    )

            with c6:
                render_html(
                    f"""
                    <div class="password-card">
                        <div class="password-value">{expiry}</div>
                    </div>
                    """
                )

            # ------------------------------------------------
            # ACTIONS
            # ------------------------------------------------

            with c7:

                (action1, action2, action3, action4) = st.columns(4)

                with action1:
                    if st.button(
                        "👁",
                        key=f"view_{record.id}",
                        help="View Password"
                    ):
                        st.session_state["current_view_id"] = record.id
                        st.rerun()

                with action2:
                    if st.button(
                        "✏",
                        key=f"edit_{record.id}",
                        help="Edit Password"
                    ):
                        st.session_state["editing_password_id"] = record.id
                        st.rerun()

                with action3:
                    favorite_icon = "⭐" if record.favorite else "☆"
                    if st.button(
                        favorite_icon,
                        key=f"favorite_{record.id}",
                        help=(
                            "Remove Favorite"
                            if record.favorite
                            else "Add Favorite"
                        )
                    ):
                        try:
                            record.favorite = not bool(record.favorite)
                            db.commit()

                            audit(
                                user_id=get_user_id(current_user),
                                action=(
                                    "PASSWORD_FAVORITED"
                                    if record.favorite
                                    else "PASSWORD_UNFAVORITED"
                                ),
                                target=(
                                    f"Favorited password: {record.title or 'Untitled'}"
                                    if record.favorite
                                    else f"Unfavorited password: {record.title or 'Untitled'}"
                                ),
                                target_type="PASSWORD",
                                target_id=record.id,
                            )
                            st.rerun()
                        except Exception as e:
                            db.rollback()
                            st.error("Could not update favorite.")
                            st.exception(e)

                with action4:
                    if st.button(
                        "🗑",
                        key=f"delete_{record.id}",
                        help="Delete Password"
                    ):
                        st.session_state["delete_password_id"] = record.id
                        st.rerun()

        # ====================================================
        # DELETE CONFIRMATION
        # ====================================================

        delete_id = st.session_state.get("delete_password_id")

        if delete_id:

            delete_record = (
                db.query(models.Password)
                .filter(
                    models.Password.id == delete_id,
                    models.Password.vault_id == vault.id
                )
                .first()
            )

            if delete_record:

                safe_delete_title = html.escape(
                    delete_record.title or "this password"
                )

                render_html(
                    f"""
                    <div class="delete-warning">
                        Are you sure you want to permanently
                        delete <b>{safe_delete_title}</b>?
                    </div>
                    """
                )

                yes, no = st.columns(2)

                with yes:
                    if st.button(
                        "Yes, Delete Password",
                        type="primary",
                        use_container_width=True,
                        key=f"confirm_delete_{delete_id}"
                    ):
                        delete_password(db, delete_record, current_user)

                with no:
                    if st.button(
                        "Cancel",
                        use_container_width=True,
                        key=f"cancel_delete_{delete_id}"
                    ):
                        st.session_state.pop("delete_password_id", None)
                        st.rerun()

            else:
                st.session_state.pop("delete_password_id", None)

        # ====================================================
        # EDIT FORM
        # ====================================================

        edit_id = st.session_state.get("editing_password_id")

        if edit_id:

            edit_record = (
                db.query(models.Password)
                .filter(
                    models.Password.id == edit_id,
                    models.Password.vault_id == vault.id
                )
                .first()
            )

            if edit_record:
                st.divider()
                show_edit_form(db, edit_record, current_user)
            else:
                st.session_state.pop("editing_password_id", None)

    except Exception as e:
        st.error("An unexpected error occurred while loading your vault.")
        st.exception(e)

    finally:
        db.close()