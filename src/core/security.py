import os
import base64
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from src.core.exceptions import SecurityError
from src.core.logger import logger

class SecurityManager:
    """Handles encryption, decryption, and key derivation."""

    SALT_SIZE = 16
    ITERATIONS = 100000

    @staticmethod
    def generate_salt() -> bytes:
        """Generates a random salt."""
        return os.urandom(SecurityManager.SALT_SIZE)

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """Derives a safe key from the password using PBKDF2HMAC."""
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=SecurityManager.ITERATIONS,
                backend=default_backend()
            )
            return base64.urlsafe_b64encode(kdf.derive(password.encode()))
        except Exception as e:
            logger.error(f"Key derivation failed: {e}")
            raise SecurityError("Failed to derive key.") from e

    @staticmethod
    def encrypt(data: bytes, key: bytes) -> bytes:
        """Encrypts data using Fernet (symmetric encryption)."""
        try:
            f = Fernet(key)
            return f.encrypt(data)
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise SecurityError("Encryption failed.") from e

    @staticmethod
    def hash_key(key: bytes) -> bytes:
        """Hashes the key to create a verifier for login (never store key directly)."""
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(key)
        return digest.finalize()

    @staticmethod
    def decrypt(token: bytes, key: bytes) -> bytes:
        """Decrypts data using Fernet."""
        try:
            f = Fernet(key)
            return f.decrypt(token)
        except InvalidToken:
            logger.warning("Decryption failed: Invalid Token (Wrong Password or Corrupted Data)")
            raise SecurityError("Invalid password or corrupted data.")
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise SecurityError("Decryption failed.") from e
