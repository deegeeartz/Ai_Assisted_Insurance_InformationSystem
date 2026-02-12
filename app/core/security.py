from cryptography.fernet import Fernet
import os

# In production, this KEY must be stored in a Secure Vault (AWS KMS, HashiCorp Vault).
# For the prototype, we generate it or read from env.
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())

cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def encrypt_data(data: bytes) -> bytes:
    return cipher_suite.encrypt(data)

def decrypt_data(encrypted_data: bytes) -> bytes:
    return cipher_suite.decrypt(encrypted_data)
