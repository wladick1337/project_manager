from pwdlib import PasswordHash

# Initializes the recommended password hashing scheme (Argon2id)
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Takes a plain text password and returns a secure, salted hash."""
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against the stored database hash."""
    return password_hash.verify(plain_password, hashed_password)