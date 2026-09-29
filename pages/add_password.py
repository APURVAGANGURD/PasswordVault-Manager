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
from security.password_generator import generate_password
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
    .page-title {
        font-size: 26px;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 4px;
        letter-spacing: -0.4px;
    }
    .page-subtitle {
        color: #94a3b8;
        font-size: 13.5px;
        margin-bottom: 20px;
    }
    .section-title {
        font-size: 15px;
        font-weight: 700;
        color: #f8fafc;
        margin-top: 16px;
        margin-bottom: 12px;
    }

    /* Cards */
    .form-card, .generator-card {
        border: 1px solid rgba(56, 189, 248, 0.18);
        border-radius: 14px;
        padding: 22px;
        background: rgba(13, 22, 42, 0.78);
        backdrop-filter: blur(16px);
        margin-bottom: 14px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
    }
    .card-title {
        font-size: 16px;
        font-weight: 700;
        color: #f8fafc;
        margin-bottom: 4px;
    }
    .card-description {
        color: #94a3b8;
        font-size: 13px;
        margin-bottom: 0;
    }

    /* Password result */
    .password-result {
        background: rgba(13, 22, 42, 0.85);
        border: 1px solid rgba(56, 189, 248, 0.25);
        border-radius: 10px;
        padding: 14px 16px;
        margin-top: 14px;
        margin-bottom: 10px;
    }
    .password-result-label {
        color: #94a3b8;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        margin-bottom: 6px;
    }
    .password-result-value {
        color: #38bdf8;
        font-family: "JetBrains Mono", monospace;
        font-size: 15px;
        font-weight: 700;
        letter-spacing: 1.5px;
        word-break: break-all;
        line-height: 1.5;
    }

    /* Tips */
    .password-tips {
        background: rgba(13, 22, 42, 0.65);
        border: 1px solid rgba(56, 189, 248, 0.15);
        border-radius: 10px;
        padding: 16px;
        margin-top: 16px;
    }
    .password-tips-title {
        color: #f8fafc;
        font-size: 13.5px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .password-tip {
        color: #94a3b8;
        font-size: 12.5px;
        margin: 5px 0;
    }
</style>
"""
    )


# ============================================================
# VAULT
# ============================================================

def get_personal_vault(db, user):
    user_id = None
    if isinstance(user, dict):
        user_id = user.get("id")

    if user_id is not None:
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
            name="Personal Vault",
            vault_type="PERSONAL"
        )
        db.add(vault)
        db.commit()
        db.refresh(vault)
        return vault

    vault = (
        db.query(models.Vault)
        .filter(models.Vault.vault_type == "PERSONAL")
        .first()
    )
    if vault:
        return vault

    vault = models.Vault(
        owner_id=1,
        name="Personal Vault",
        vault_type="PERSONAL"
    )
    db.add(vault)
    db.commit()
    db.refresh(vault)
    return vault


# ============================================================
# PAGE
# ============================================================

def show(user):
    load_css()

    render_html(
        '<div class="page-title">Add Password</div>'
    )
    render_html(
        '<div class="page-subtitle">Securely save a new password to your personal vault.</div>'
    )

    if st.button("← Back to My Vault"):
        st.session_state["nav"] = "My Vault"
        st.rerun()

    db = next(get_db())
    vault = get_personal_vault(db, user)

    # ========================================================
    # LAYOUT
    # ========================================================

    left, right = st.columns([1.55, 1])

    # ========================================================
    # FORM
    # ========================================================

    with left:
        render_html(
            '<div class="form-card">'
            '<div class="card-title">Password Details</div>'
            '</div>'
        )

        with st.form("add_password_form", clear_on_submit=False):
            title = st.text_input("Title *", placeholder="My Gmail Account")
            username = st.text_input("Username *", placeholder="name@example.com")

            generated_password = st.session_state.get("generated_password", "")

            password = st.text_input(
                "Password *",
                value=generated_password,
                type="password",
                placeholder="Enter password"
            )

            url = st.text_input("Website URL", placeholder="https://example.com")

            category = st.selectbox(
                "Category",
                [
                    "Work", "Social", "Development", "Cloud",
                    "Finance", "Database", "Entertainment", "Other"
                ]
            )

            expiry = st.date_input("Expiry Date", value=None)
            notes = st.text_area("Notes", placeholder="Add notes...")

            st.write("")

            save = st.form_submit_button(
                "💾 Save Password",
                use_container_width=True,
                type="primary"
            )

            if save:
                if not title.strip():
                    st.error("Title is required.")
                elif not username.strip():
                    st.error("Username is required.")
                elif not password:
                    st.error("Password is required.")
                else:
                    try:
                        encrypted_password, nonce = VaultEncryption.encrypt_data(
                            password, GLOBAL_KEY
                        )

                        new_record = models.Password(
                            vault_id=vault.id,
                            title=title.strip(),
                            username=username.strip(),
                            encrypted_password=encrypted_password,
                            encryption_nonce=nonce,
                            url=url.strip() if url else None,
                            category=category,
                            expiry_date=expiry,
                            encrypted_notes=(
                                notes.encode("utf-8") if notes else None
                            ),
                            favorite=False
                        )

                        db.add(new_record)
                        db.commit()
                        db.refresh(new_record)

                        st.session_state.pop("generated_password", None)

                        st.success("✅ Password saved successfully!")
                        time.sleep(0.8)
                        st.session_state["nav"] = "My Vault"
                        st.rerun()

                    except Exception as e:
                        db.rollback()
                        st.error("Failed to save password.")
                        st.exception(e)

    # ========================================================
    # GENERATOR
    # ========================================================

    with right:
        render_html(
            '<div class="generator-card">'
            '<div class="card-title">Password Generator</div>'
            '<p class="card-description">Generate a strong password automatically.</p>'
            '</div>'
        )

        length = st.slider("Password Length", 8, 64, 16)

        if st.button("🔄 Generate Password", use_container_width=True):
            st.session_state["generated_password"] = generate_password(length)
            st.rerun()

        generated = st.session_state.get("generated_password")

        if generated:
            strength = estimate_strength(generated)

            render_html(
                f'<div class="password-result">'
                f'<div class="password-result-label">Generated Password</div>'
                f'<div class="password-result-value">{generated}</div>'
                f'</div>'
            )

            st.markdown(f"**Strength:** {strength['label']}")

            st.info(
                "The generated password will automatically "
                "appear in the Password field."
            )
        else:
            st.info(
                "Click Generate Password to create a secure password."
            )

        render_html(
            '<div class="password-tips">'
            '<div class="password-tips-title">Password recommendations</div>'
            '<div class="password-tip">✓ Use at least 12 characters</div>'
            '<div class="password-tip">✓ Use uppercase and lowercase letters</div>'
            '<div class="password-tip">✓ Include numbers</div>'
            '<div class="password-tip">✓ Include special characters</div>'
            '<div class="password-tip">✓ Don\'t reuse passwords</div>'
            '<div class="password-tip">✓ Don\'t use personal information</div>'
            '</div>'
        )