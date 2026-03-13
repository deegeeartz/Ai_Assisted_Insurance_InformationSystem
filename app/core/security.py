from cryptography.fernet import Fernet
from functools import lru_cache
from app.core.config import settings

@lru_cache(maxsize=1)
def get_cipher_suite() -> Fernet:
    try:
        return Fernet(settings.encryption_key.encode())
    except Exception as exc:
        raise RuntimeError("Invalid or missing ENCRYPTION_KEY configuration.") from exc


def encrypt_data(data: bytes) -> bytes:
    return get_cipher_suite().encrypt(data)

def decrypt_data(encrypted_data: bytes) -> bytes:
    return get_cipher_suite().decrypt(encrypted_data)
