import pytest
import os
from src.core.security import SecurityManager
from src.core.exceptions import SecurityError

def test_generate_salt():
    salt1 = SecurityManager.generate_salt()
    salt2 = SecurityManager.generate_salt()
    assert len(salt1) == 16
    assert salt1 != salt2

def test_derive_key():
    password = "securepassword"
    salt = os.urandom(16)
    key1 = SecurityManager.derive_key(password, salt)
    key2 = SecurityManager.derive_key(password, salt)
    assert key1 == key2

def test_encrypt_decrypt():
    key = SecurityManager.derive_key("password", os.urandom(16))
    data = b"Secret Data"
    encrypted = SecurityManager.encrypt(data, key)
    decrypted = SecurityManager.decrypt(encrypted, key)
    assert decrypted == data

def test_decrypt_invalid_key():
    key1 = SecurityManager.derive_key("password", os.urandom(16))
    key2 = SecurityManager.derive_key("wrongpassword", os.urandom(16))
    data = b"Secret Data"
    encrypted = SecurityManager.encrypt(data, key1)
    
    with pytest.raises(SecurityError):
        SecurityManager.decrypt(encrypted, key2)
