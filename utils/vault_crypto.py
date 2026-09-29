# ============================================================
# utils/vault_crypto.py
# Centralized vault encryption / decryption
# ============================================================

from security.encryption import VaultEncryption
from security.key_manager import KeyManager


# ============================================================
# MASTER KEY
# ------------------------------------------------------------
# IMPORTANT:
# This must be the SAME key used by:
#   - pages/add_password.py
#   - pages/view_password.py
#   - pages/dashboard.py
#   - pages/password_health.py
#
# Do NOT change this value unless you also re-encrypt every
# existing password in the database.
# ============================================================

GLOBAL_KEY = KeyManager.derive_key(
    "FIXED_KEY_123",
    "FIXED_SALT_123"
)


# ============================================================
# ENCRYPT / DECRYPT TEXT
# ============================================================

def encrypt_text(plain_text: str):
    """
    Encrypt any string (password).
    Returns: (ciphertext_bytes, nonce_bytes)
    """
    if plain_text is None:
        plain_text = ""

    if not isinstance(plain_text, str):
        plain_text = str(plain_text)

    ciphertext, nonce = VaultEncryption.encrypt_data(plain_text, GLOBAL_KEY)
    return ciphertext, nonce


def decrypt_text(ciphertext, nonce) -> str:
    """
    Decrypt text back to a plain string.
    Raises on failure.
    """
    if ciphertext is None:
        return ""

    return VaultEncryption.decrypt_data(ciphertext, nonce, GLOBAL_KEY)


# ============================================================
# ENCRYPT / DECRYPT NOTES
# ------------------------------------------------------------
# `notes` are stored in the DB as bytes in the format:
#     nonce_hex : ciphertext_hex
# (as UTF-8 encoded text)
# ============================================================

def encrypt_notes(plain_notes: str):
    """
    Encrypt notes and return (encrypted_hex_string, nonce_hex_string).
    The caller combines them into "nonce:ciphertext" format.
    """
    if not plain_notes:
        return None, None

    ciphertext, nonce = VaultEncryption.encrypt_data(plain_notes, GLOBAL_KEY)

    # Return hex strings (as expected by my_vault.py)
    return ciphertext.hex(), nonce.hex()


def decrypt_notes(encrypted_hex, nonce_hex) -> str:
    """
    Decrypt notes.
    Accepts hex strings (as produced by encrypt_notes).
    """
    if not encrypted_hex or not nonce_hex:
        return ""

    try:
        ciphertext = bytes.fromhex(encrypted_hex)
        nonce = bytes.fromhex(nonce_hex)
        return VaultEncryption.decrypt_data(ciphertext, nonce, GLOBAL_KEY)
    except Exception:
        return ""


__all__ = [
    "encrypt_text",
    "decrypt_text",
    "encrypt_notes",
    "decrypt_notes",
    "GLOBAL_KEY",
]