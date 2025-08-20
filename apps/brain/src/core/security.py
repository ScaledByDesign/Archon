"""
Security utilities and helpers for the FastAPI backend
Provides password hashing, token generation, and security validation
"""

import secrets
import string
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import hashlib
import hmac
import base64

from passlib.context import CryptContext
from passlib.hash import bcrypt
import jwt
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Stored password hash
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a cryptographically secure random token
    
    Args:
        length: Length of the token in bytes
        
    Returns:
        URL-safe base64 encoded token
    """
    return secrets.token_urlsafe(length)


def generate_api_key(prefix: str = "rag", length: int = 32) -> str:
    """
    Generate an API key with a specific prefix
    
    Args:
        prefix: Prefix for the API key
        length: Length of the random part
        
    Returns:
        API key in format: prefix_randomstring
    """
    random_part = secrets.token_urlsafe(length)
    return f"{prefix}_{random_part}"


def generate_password(
    length: int = 16,
    include_uppercase: bool = True,
    include_lowercase: bool = True,
    include_digits: bool = True,
    include_symbols: bool = True,
    exclude_ambiguous: bool = True
) -> str:
    """
    Generate a secure random password
    
    Args:
        length: Password length
        include_uppercase: Include uppercase letters
        include_lowercase: Include lowercase letters
        include_digits: Include digits
        include_symbols: Include symbols
        exclude_ambiguous: Exclude ambiguous characters (0, O, l, I, etc.)
        
    Returns:
        Generated password
    """
    characters = ""
    
    if include_lowercase:
        chars = string.ascii_lowercase
        if exclude_ambiguous:
            chars = chars.replace('l', '').replace('o', '')
        characters += chars
    
    if include_uppercase:
        chars = string.ascii_uppercase
        if exclude_ambiguous:
            chars = chars.replace('I', '').replace('O', '')
        characters += chars
    
    if include_digits:
        chars = string.digits
        if exclude_ambiguous:
            chars = chars.replace('0', '').replace('1', '')
        characters += chars
    
    if include_symbols:
        chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        characters += chars
    
    if not characters:
        raise ValueError("At least one character type must be included")
    
    # Ensure at least one character from each selected type
    password = []
    if include_lowercase:
        password.append(secrets.choice(string.ascii_lowercase))
    if include_uppercase:
        password.append(secrets.choice(string.ascii_uppercase))
    if include_digits:
        password.append(secrets.choice(string.digits))
    if include_symbols:
        password.append(secrets.choice("!@#$%^&*()_+-=[]{}|;:,.<>?"))
    
    # Fill the rest with random characters
    for _ in range(length - len(password)):
        password.append(secrets.choice(characters))
    
    # Shuffle the password
    secrets.SystemRandom().shuffle(password)
    
    return ''.join(password)


def create_signature(
    data: str,
    secret: str,
    algorithm: str = "sha256"
) -> str:
    """
    Create HMAC signature for data
    
    Args:
        data: Data to sign
        secret: Secret key for signing
        algorithm: Hash algorithm to use
        
    Returns:
        Base64 encoded signature
    """
    secret_bytes = secret.encode('utf-8')
    data_bytes = data.encode('utf-8')
    
    signature = hmac.new(
        secret_bytes,
        data_bytes,
        getattr(hashlib, algorithm)
    ).digest()
    
    return base64.b64encode(signature).decode('utf-8')


def verify_signature(
    data: str,
    signature: str,
    secret: str,
    algorithm: str = "sha256"
) -> bool:
    """
    Verify HMAC signature
    
    Args:
        data: Original data
        signature: Signature to verify
        secret: Secret key used for signing
        algorithm: Hash algorithm used
        
    Returns:
        True if signature is valid, False otherwise
    """
    try:
        expected_signature = create_signature(data, secret, algorithm)
        return hmac.compare_digest(signature, expected_signature)
    except Exception:
        return False


def derive_key(
    password: str,
    salt: bytes,
    length: int = 32,
    iterations: int = 100000
) -> bytes:
    """
    Derive a key from a password using PBKDF2
    
    Args:
        password: Password to derive key from
        salt: Salt bytes
        length: Length of derived key
        iterations: Number of iterations
        
    Returns:
        Derived key bytes
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=length,
        salt=salt,
        iterations=iterations,
    )
    return kdf.derive(password.encode('utf-8'))


def constant_time_compare(a: str, b: str) -> bool:
    """
    Compare two strings in constant time to prevent timing attacks
    
    Args:
        a: First string
        b: Second string
        
    Returns:
        True if strings are equal, False otherwise
    """
    return hmac.compare_digest(a, b)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal attacks
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove path separators and dangerous characters
    dangerous_chars = ['/', '\\', '..', '~', '$', '&', '|', ';', '`']
    sanitized = filename
    
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure filename is not empty
    if not sanitized:
        sanitized = "unnamed_file"
    
    # Limit length
    if len(sanitized) > 255:
        name, ext = sanitized.rsplit('.', 1) if '.' in sanitized else (sanitized, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        sanitized = name[:max_name_length] + ('.' + ext if ext else '')
    
    return sanitized


def validate_email(email: str) -> bool:
    """
    Basic email validation
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email appears valid, False otherwise
    """
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> Dict[str, Any]:
    """
    Validate password strength
    
    Args:
        password: Password to validate
        
    Returns:
        Dictionary with validation results
    """
    result = {
        "valid": True,
        "score": 0,
        "issues": [],
        "suggestions": []
    }
    
    # Length check
    if len(password) < 8:
        result["valid"] = False
        result["issues"].append("Password must be at least 8 characters long")
    elif len(password) >= 12:
        result["score"] += 2
    else:
        result["score"] += 1
    
    # Character type checks
    has_lower = any(c.islower() for c in password)
    has_upper = any(c.isupper() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_symbol = any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    
    char_types = sum([has_lower, has_upper, has_digit, has_symbol])
    
    if char_types < 3:
        result["valid"] = False
        result["issues"].append("Password must contain at least 3 different character types")
    
    result["score"] += char_types
    
    # Common password check (basic)
    common_passwords = [
        "password", "123456", "password123", "admin", "qwerty",
        "letmein", "welcome", "monkey", "dragon", "master"
    ]
    
    if password.lower() in common_passwords:
        result["valid"] = False
        result["issues"].append("Password is too common")
        result["score"] = 0
    
    # Repetition check
    if len(set(password)) < len(password) * 0.6:
        result["issues"].append("Password has too many repeated characters")
        result["score"] -= 1
    
    # Suggestions
    if not has_lower:
        result["suggestions"].append("Add lowercase letters")
    if not has_upper:
        result["suggestions"].append("Add uppercase letters")
    if not has_digit:
        result["suggestions"].append("Add numbers")
    if not has_symbol:
        result["suggestions"].append("Add special characters")
    if len(password) < 12:
        result["suggestions"].append("Use at least 12 characters")
    
    # Final score adjustment
    result["score"] = max(0, min(10, result["score"]))
    
    return result


def generate_csrf_token() -> str:
    """
    Generate a CSRF token
    
    Returns:
        CSRF token string
    """
    return generate_secure_token(32)


def create_session_token(
    user_id: str,
    secret_key: str,
    expires_in: int = 3600
) -> str:
    """
    Create a signed session token
    
    Args:
        user_id: User identifier
        secret_key: Secret key for signing
        expires_in: Token expiration time in seconds
        
    Returns:
        Signed session token
    """
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(seconds=expires_in),
        "iat": datetime.utcnow(),
        "type": "session"
    }
    
    return jwt.encode(payload, secret_key, algorithm="HS256")


def verify_session_token(
    token: str,
    secret_key: str
) -> Optional[Dict[str, Any]]:
    """
    Verify and decode a session token
    
    Args:
        token: Session token to verify
        secret_key: Secret key used for signing
        
    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        if payload.get("type") != "session":
            return None
        return payload
    except jwt.InvalidTokenError:
        return None
