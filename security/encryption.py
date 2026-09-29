from cryptography.hazmat.primitives.ciphers.aead import AESGCM
import os


class VaultEncryption:

    @staticmethod
    def encrypt_data(
        data: str,
        key: bytes
    ) -> tuple:
        """
        Encrypt text using AES-256-GCM.

        Returns:
            ciphertext, nonce
        """

        if data is None:
            data = ""

        if not isinstance(data, str):
            data = str(data)

        if not isinstance(key, bytes):
            raise TypeError(
                "Encryption key must be bytes."
            )

        if len(key) != 32:
            raise ValueError(
                f"Encryption key must be 32 bytes. "
                f"Got {len(key)} bytes."
            )

        aesgcm = AESGCM(key)

        # AES-GCM standard 96-bit nonce
        nonce = os.urandom(12)

        ciphertext = aesgcm.encrypt(
            nonce,
            data.encode("utf-8"),
            None
        )

        return ciphertext, nonce

    @staticmethod
    def decrypt_data(
        ciphertext: bytes,
        nonce: bytes,
        key: bytes
    ) -> str:
        """
        Decrypt AES-256-GCM data.
        """

        if ciphertext is None:
            raise ValueError(
                "Encrypted password is missing."
            )

        if nonce is None:
            raise ValueError(
                "Encryption nonce is missing."
            )

        if not isinstance(key, bytes):
            raise TypeError(
                "Decryption key must be bytes."
            )

        if len(key) != 32:
            raise ValueError(
                f"Decryption key must be 32 bytes. "
                f"Got {len(key)} bytes."
            )

        aesgcm = AESGCM(key)

        plaintext = aesgcm.decrypt(
            nonce,
            ciphertext,
            None
        )

        return plaintext.decode("utf-8")