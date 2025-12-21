"""
Password hashing utilities - Laravel Hash facade style
"""

import bcrypt


def _hash_password(password: str) -> str:
    """Hash password using bcrypt directly"""
    # Ensure password is not longer than 72 bytes (bcrypt limit)
    if len(password.encode("utf-8")) > 72:
        password = password[:72]

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def _verify_password(password: str, hashed: str) -> bool:
    """Verify password using bcrypt directly"""
    # Ensure password is not longer than 72 bytes (bcrypt limit)
    if len(password.encode("utf-8")) > 72:
        password = password[:72]

    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


class Hash:
    """
    Password hashing facade - Laravel equivalent: Hash::make(), Hash::check()
    """

    @staticmethod
    def make(password: str) -> str:
        """
        Hash a password.
        Laravel equivalent: Hash::make($password)
        """
        return _hash_password(password)

    @staticmethod
    def check(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hash.
        Laravel equivalent: Hash::check($password, $hash)
        """
        return _verify_password(plain_password, hashed_password)

    @staticmethod
    def needs_rehash(hashed_password: str) -> bool:
        """
        Check if password needs rehashing.
        Laravel equivalent: Hash::needsRehash($hash)
        """
        # Simple implementation - bcrypt hashes are generally stable
        return False


# Convenience functions (Laravel style)
def make_password(password: str) -> str:
    """Hash a password"""
    return _hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password"""
    return _verify_password(plain_password, hashed_password)
