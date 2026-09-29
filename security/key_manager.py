from argon2.low_level import (
    hash_secret_raw,
    Type
)


class KeyManager:

    @staticmethod
    def derive_key(
        master_password: str,
        salt: str
    ) -> bytes:
        """
        Derive a deterministic 32-byte AES-256 key
        using Argon2id.

        IMPORTANT:
        The same password + salt produces the same key.
        """

        if not master_password:
            raise ValueError(
                "Master password cannot be empty."
            )

        if not salt:
            raise ValueError(
                "Salt cannot be empty."
            )

        key = hash_secret_raw(
            secret=master_password.encode("utf-8"),
            salt=salt.encode("utf-8"),
            time_cost=3,
            memory_cost=65536,
            parallelism=4,
            hash_len=32,
            type=Type.ID
        )

        return key