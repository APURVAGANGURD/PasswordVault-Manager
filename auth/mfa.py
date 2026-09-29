# ============================================================
# auth/mfa.py
# SecureVault Manager
# EMAIL OTP ONLY
# ============================================================

import secrets
import hmac


# ============================================================
# GENERATE OTP
# ============================================================

def generate_otp():
    """
    Generate secure 6 digit OTP.
    """

    return f"{secrets.randbelow(1000000):06d}"


# ============================================================
# VERIFY OTP
# ============================================================

def verify_otp(
    entered_otp,
    stored_otp
):
    """
    Secure OTP comparison.
    """

    if not entered_otp:
        return False

    if not stored_otp:
        return False

    return hmac.compare_digest(
        str(entered_otp).strip(),
        str(stored_otp).strip()
    )


# ============================================================
# IMPORTANT
# ============================================================
#
# There is intentionally:
#
# NO pyotp
# NO qrcode
# NO TOTP
# NO authenticator application
# NO QR code
#
# SecureVault uses Email OTP only.
# ============================================================