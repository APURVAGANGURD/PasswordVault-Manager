import streamlit as st
import sys
import os
import time

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from database.connection import get_db
from database import models
from security.encryption import VaultEncryption
from security.key_manager import KeyManager
from security.password_strength import estimate_strength
from utils.theme import inject_cyber_theme, render_html


# ============================================================
# DEVELOPMENT KEY
# ============================================================

GLOBAL_KEY = KeyManager.derive_key(
    "FIXED_KEY_123",
    "FIXED_SALT_123"
)


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

    /* Detail cards */
    .detail-card {
        background: rgba(13, 22, 42, 0.78);
        border: 1px solid rgba(56, 189, 248, 0.18);
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 16px;
        backdrop-filter: blur(16px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
    }
    .detail-label {
        font-size: 11.5px;
        color: #94a3b8;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-bottom: 5px;
    }
    .detail-value {
        font-size: 14.5px;
        color: #f8fafc;
        margin-bottom: 18px;
        word-break: break-word;
    }
    .password-box {
        background: rgba(13, 22, 42, 0.85);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 10px;
        padding: 12px 16px;
        color: #38bdf8;
        font-size: 15px;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 1.5px;
        margin-bottom: 12px;
        word-break: break-all;
    }

    /* Metadata card */
    .metadata-card {
        background: rgba(13, 22, 42, 0.65);
        border: 1px solid rgba(56, 189, 248, 0.15);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 15px;
    }
    .metadata-title {
        font-size: 15px;
        font-weight: 700;
        color: #f8fafc;
    }

    /* Strength badges */
    .strength {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 10.5px;
        font-weight: 700;
        letter-spacing: 0.3px;
    }
    .strength-strong { background: rgba(16, 185, 129, 0.14); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.35); }
    .strength-medium { background: rgba(245, 158, 11, 0.14); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.35); }
    .strength-weak { background: rgba(244, 63, 94, 0.14); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.35); }
    .strength-very-weak { background: rgba(244, 63, 94, 0.22); color: #f43f5e; border: 1px solid rgba(244, 63, 94, 0.5); }

    /* Info card */
    .info-card {
        background: rgba(13, 22, 42, 0.7);
        border: 1px solid rgba(56, 189, 248, 0.18);
        border-radius: 10px;
        padding: 14px 16px;
        margin: 15px 0;
        color: #94a3b8;
        font-size: 13px;
    }
</style>
"""
    )
# ============================================================
# STRENGTH
# ============================================================

def get_strength_class(label):

    label = str(label).lower()

    if "very weak" in label:
        return "strength-very-weak"

    if "weak" in label:
        return "strength-weak"

    if (
        "medium" in label
        or "moderate" in label
    ):
        return "strength-medium"

    return "strength-strong"


# ============================================================
# PAGE
# ============================================================

def show(user, password_id):

    load_css()

    db = next(get_db())

    # ========================================================
    # VALIDATE ID
    # ========================================================

    if not password_id:

        st.error(
            "No password was selected."
        )

        if st.button("← Back to My Vault"):

            st.session_state["nav"] = "My Vault"
            st.rerun()

        return

    # ========================================================
    # GET PASSWORD
    # ========================================================

    record = (
        db.query(models.Password)
        .filter(
            models.Password.id == password_id
        )
        .first()
    )

    if not record:

        st.error(
            "Password record not found."
        )

        if st.button("← Back to My Vault"):

            st.session_state["nav"] = "My Vault"
            st.rerun()

        return

    # ========================================================
    # DECRYPT
    # ========================================================

    try:

        plain_password = (
            VaultEncryption.decrypt_data(
                record.encrypted_password,
                record.encryption_nonce,
                GLOBAL_KEY
            )
        )

        strength = estimate_strength(
            plain_password
        )

    except Exception as e:

        st.error(
            "Unable to decrypt this password."
        )

        st.warning(
            f"{type(e).__name__}: {repr(e)}"
        )

        st.info(
            "If this password was created before the "
            "KeyManager fix, delete it and create it again."
        )

        if st.button("← Back to My Vault"):

            st.session_state["nav"] = "My Vault"

            st.rerun()

        return

    # ========================================================
    # BACK
    # ========================================================

    if st.button("← Back to My Vault"):

        st.session_state["nav"] = "My Vault"

        st.rerun()

    # ========================================================
    # TITLE
    # ========================================================

    render_html(
        '<div class="page-title">'
        'View Password'
        '</div>'
    )

    render_html(
        '<div class="page-subtitle">'
        'View and manage your saved password.'
        '</div>'
    )

    # ========================================================
    # PASSWORD VISIBILITY
    # ========================================================

    visibility_key = (
        f"password_visible_{record.id}"
    )

    if visibility_key not in st.session_state:

        st.session_state[
            visibility_key
        ] = False

    # ========================================================
    # LAYOUT
    # ========================================================

    left, right = st.columns(
        [2, 1]
    )

    # ========================================================
    # LEFT
    # ========================================================

    with left:

        render_html(
            '<div class="detail-card">'
        )

        # TITLE
        render_html(
            '<div class="detail-label">'
            'Title'
            '</div>'
        )

        render_html(
            f'<div class="detail-value">'
            f'{record.title or "-"}'
            f'</div>'
        )

        # USERNAME
        render_html(
            '<div class="detail-label">'
            'Username'
            '</div>'
        )

        render_html(
            f'<div class="detail-value">'
            f'{record.username or "-"}'
            f'</div>'
        )

        # PASSWORD
        render_html(
            '<div class="detail-label">'
            'Password'
            '</div>'
        )

        if st.session_state[
            visibility_key
        ]:

            display_password = plain_password

        else:

            display_password = (
                "••••••••••••••••"
            )

        render_html(
            f"""
<div class="password-box">
{display_password}
</div>
"""
        )

        pw1, pw2 = st.columns(2)

        with pw1:

            visibility_text = (
                "🙈 Hide Password"
                if st.session_state[
                    visibility_key
                ]
                else "👁 Show Password"
            )

            if st.button(
                visibility_text,
                use_container_width=True
            ):

                st.session_state[
                    visibility_key
                ] = not st.session_state[
                    visibility_key
                ]

                st.rerun()

        with pw2:

            if st.button(
                "📋 Copy Password",
                use_container_width=True
            ):

                # Streamlit itself doesn't expose a universal
                # browser clipboard API through st.button.
                # Show the value in a selectable code block.
                st.code(
                    plain_password
                )

                st.info(
                    "Select and copy the password above."
                )

        # STRENGTH
        render_html(
            '<div class="detail-label">'
            'Password Strength'
            '</div>'
        )

        strength_class = get_strength_class(
            strength["label"]
        )

        render_html(
            f"""
<span class="strength {strength_class}">
{str(strength["label"]).upper()}
</span>
"""
        )

        st.write("")

        # URL
        render_html(
            '<div class="detail-label">'
            'Website URL'
            '</div>'
        )

        if record.url:

            render_html(
                f"""
<div class="detail-value">
<a href="{record.url}" target="_blank">
{record.url}
</a>
</div>
"""
            )

        else:

            render_html(
                '<div class="detail-value">-</div>'
            )

        # CATEGORY / EXPIRY
        c1, c2 = st.columns(2)

        with c1:

            render_html(
                '<div class="detail-label">'
                'Category'
                '</div>'
            )

            render_html(
                f'<div class="detail-value">'
                f'{record.category or "-"}'
                f'</div>'
            )

        with c2:

            render_html(
                '<div class="detail-label">'
                'Expiry Date'
                '</div>'
            )

            expiry = (
                record.expiry_date.strftime(
                    "%Y-%m-%d"
                )
                if record.expiry_date
                else "-"
            )

            render_html(
                f'<div class="detail-value">'
                f'{expiry}'
                f'</div>'
            )

        # NOTES
        render_html(
            '<div class="detail-label">'
            'Notes'
            '</div>'
        )

        try:

            notes = (
                record.encrypted_notes.decode(
                    "utf-8"
                )
                if record.encrypted_notes
                else ""
            )

        except Exception:

            notes = ""

        render_html(
            f'<div class="detail-value">'
            f'{notes or "No notes"}'
            f'</div>'
        )

        render_html(
            '</div>'
        )

        # ====================================================
        # ACTIONS
        # ====================================================

        edit, share, delete = st.columns(3)

        with edit:

            if st.button(
                "✏ Edit",
                use_container_width=True
            ):

                st.info(
                    "Edit Password page can be added next."
                )

        with share:

            if st.button(
                "🔗 Share",
                use_container_width=True
            ):

                st.info(
                    "Sharing will be connected to "
                    "Shared Vault."
                )

        with delete:

            if st.button(
                "🗑 Delete",
                use_container_width=True
            ):

                st.session_state[
                    "confirm_view_delete"
                ] = True

                st.rerun()

        # DELETE CONFIRMATION
        if st.session_state.get(
            "confirm_view_delete",
            False
        ):

            st.warning(
                f"Delete **{record.title}** permanently?"
            )

            yes, no = st.columns(2)

            with yes:

                if st.button(
                    "Yes, Delete",
                    type="primary",
                    use_container_width=True
                ):

                    db.delete(record)

                    db.commit()

                    st.session_state.pop(
                        "confirm_view_delete",
                        None
                    )

                    st.session_state[
                        "nav"
                    ] = "My Vault"

                    st.success(
                        "Password deleted."
                    )

                    time.sleep(0.7)

                    st.rerun()

            with no:

                if st.button(
                    "Cancel",
                    use_container_width=True
                ):

                    st.session_state.pop(
                        "confirm_view_delete",
                        None
                    )

                    st.rerun()

    # ========================================================
    # RIGHT
    # ========================================================

    with right:

        render_html(
            """
<div class="metadata-card">

<div class="metadata-title">
    Password Details
</div>

</div>
"""
        )

        st.markdown(
            "**Created At**"
        )

        st.caption(
            str(record.created_at)
            if record.created_at
            else "-"
        )

        st.markdown(
            "**Last Updated**"
        )

        st.caption(
            str(record.updated_at)
            if record.updated_at
            else "-"
        )

        st.markdown(
            "**Vault**"
        )

        st.caption(
            "Personal Vault"
        )

        st.markdown(
            "**Password ID**"
        )

        st.caption(
            str(record.id)
        )

        st.markdown(
            "**Favorite**"
        )

        st.caption(
            "⭐ Yes"
            if record.favorite
            else "☆ No"
        )

    # ========================================================
    # AUDIT LOG
    # ========================================================

    audit_key = (
        f"password_view_audit_{record.id}"
    )

    if not st.session_state.get(
        audit_key,
        False
    ):

        try:

            user_id = (
                user.get("id")
                if isinstance(user, dict)
                else None
            )

            if user_id is not None:

                log = models.AuditLog(
                    user_id=user_id,
                    action="PASSWORD_VIEWED",
                    target_type="PASSWORD",
                    target_id=record.id
                )

                db.add(log)

                db.commit()

            st.session_state[
                audit_key
            ] = True

        except Exception:

            db.rollback()