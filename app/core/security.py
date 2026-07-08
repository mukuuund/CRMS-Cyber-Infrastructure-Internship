import hashlib

class NotAuthenticated(Exception):
    pass

SALT = b"simple_v1_salt"

def get_password_hash(password: str) -> str:
    """Returns a basic PBKDF2 hash of the password."""
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), SALT, 100000).hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against the stored hash."""
    return get_password_hash(plain_password) == hashed_password
