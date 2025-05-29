"""
Data validation utilities for the FastAPI backend
Provides Pydantic models and validation functions
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import re

from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator
from pydantic.types import SecretStr

# EmailStr requires email-validator package
try:
    from pydantic import EmailStr
except ImportError:
    # Fallback if email-validator is not installed
    EmailStr = str


class UserRole(str, Enum):
    """User role enumeration"""
    ADMIN = "admin"
    USER = "user"
    MODERATOR = "moderator"
    VIEWER = "viewer"


class APIKeyScope(str, Enum):
    """API key scope enumeration"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    SEARCH = "search"
    UPLOAD = "upload"


class BaseValidator(BaseModel):
    """Base validator with common configuration"""
    
    class Config:
        use_enum_values = True
        validate_assignment = True
        extra = "forbid"
        str_strip_whitespace = True


class UserCreateRequest(BaseValidator):
    """User creation request validation"""
    
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_-]+$",
        description="Username (alphanumeric, underscore, hyphen only)"
    )
    password: SecretStr = Field(
        ...,
        min_length=8,
        description="Password (minimum 8 characters)"
    )
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Full name"
    )
    roles: List[UserRole] = Field(
        default=[UserRole.USER],
        description="User roles"
    )
    
    @field_validator('username')
    def validate_username(cls, v):
        """Validate username format"""
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError("Username can only contain letters, numbers, underscore, and hyphen")
        return v.lower()
    
    @field_validator('password')
    def validate_password_strength(cls, v):
        """Validate password strength"""
        password = v.get_secret_value()
        
        # Check minimum requirements
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Check for at least one uppercase, lowercase, digit, and special char
        if not re.search(r"[A-Z]", password):
            raise ValueError("Password must contain at least one uppercase letter")
        
        if not re.search(r"[a-z]", password):
            raise ValueError("Password must contain at least one lowercase letter")
        
        if not re.search(r"\d", password):
            raise ValueError("Password must contain at least one digit")
        
        if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]", password):
            raise ValueError("Password must contain at least one special character")
        
        return v


class UserUpdateRequest(BaseValidator):
    """User update request validation"""
    
    email: Optional[EmailStr] = Field(None, description="User email address")
    full_name: Optional[str] = Field(
        None,
        max_length=100,
        description="Full name"
    )
    roles: Optional[List[UserRole]] = Field(
        None,
        description="User roles"
    )


class APIKeyCreateRequest(BaseValidator):
    """API key creation request validation"""
    
    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="API key name"
    )
    description: Optional[str] = Field(
        None,
        max_length=500,
        description="API key description"
    )
    scopes: List[APIKeyScope] = Field(
        ...,
        min_items=1,
        description="API key scopes"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="API key expiration date"
    )
    
    @field_validator('expires_at')
    def validate_expiration(cls, v):
        """Validate expiration date is in the future"""
        if v and v <= datetime.utcnow():
            raise ValueError("Expiration date must be in the future")
        return v


class SearchRequest(BaseValidator):
    """Search request validation"""
    
    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Search query"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Number of results to return"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of results to skip"
    )
    filters: Optional[Dict[str, Any]] = Field(
        None,
        description="Search filters"
    )
    include_metadata: bool = Field(
        default=False,
        description="Include metadata in results"
    )


class DocumentUploadRequest(BaseValidator):
    """Document upload request validation"""
    
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Document title"
    )
    content: str = Field(
        ...,
        min_length=1,
        description="Document content"
    )
    content_type: str = Field(
        default="text/plain",
        description="Content type"
    )
    tags: Optional[List[str]] = Field(
        None,
        description="Document tags"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Document metadata"
    )
    
    @field_validator('tags')
    def validate_tags(cls, v):
        """Validate tags format"""
        if v:
            # Limit number of tags
            if len(v) > 20:
                raise ValueError("Maximum 20 tags allowed")
            
            # Validate tag format
            for tag in v:
                if not isinstance(tag, str):
                    raise ValueError("Tags must be strings")
                if len(tag) > 50:
                    raise ValueError("Tag length cannot exceed 50 characters")
                if not re.match(r"^[a-zA-Z0-9_-]+$", tag):
                    raise ValueError("Tags can only contain letters, numbers, underscore, and hyphen")
        
        return v


class PaginationParams(BaseValidator):
    """Pagination parameters validation"""
    
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (1-based)"
    )
    size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Page size"
    )
    
    @property
    def offset(self) -> int:
        """Calculate offset from page and size"""
        return (self.page - 1) * self.size


class SortParams(BaseValidator):
    """Sort parameters validation"""
    
    sort_by: str = Field(
        default="created_at",
        description="Field to sort by"
    )
    sort_order: str = Field(
        default="desc",
        pattern=r"^(asc|desc)$",
        description="Sort order (asc or desc)"
    )


class DateRangeFilter(BaseValidator):
    """Date range filter validation"""
    
    start_date: Optional[datetime] = Field(
        None,
        description="Start date"
    )
    end_date: Optional[datetime] = Field(
        None,
        description="End date"
    )
    
    @model_validator(mode='before')
    def validate_date_range(cls, values):
        """Validate date range is logical"""
        start_date = values.get('start_date')
        end_date = values.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValueError("Start date must be before end date")
        
        return values


class DependencyStatus(BaseValidator):
    """Dependency status model"""
    
    status: str = Field(..., description="Dependency status")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Dependency details"
    )


class HealthCheckResponse(BaseValidator):
    """Health check response model"""
    
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: Optional[str] = Field(None, description="Service version")
    dependencies: Optional[Dict[str, Any]] = Field(
        None,
        description="Dependency status"
    )


class ErrorResponse(BaseValidator):
    """Error response model"""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Error details"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request ID")


class SuccessResponse(BaseValidator):
    """Success response model"""
    
    success: bool = Field(default=True)
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(
        None,
        description="Response data"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow)


def validate_file_upload(
    filename: str,
    content_type: str,
    file_size: int,
    allowed_extensions: List[str] = None,
    max_size_mb: int = 10
) -> Dict[str, Any]:
    """
    Validate file upload parameters
    
    Args:
        filename: Original filename
        content_type: MIME content type
        file_size: File size in bytes
        allowed_extensions: List of allowed file extensions
        max_size_mb: Maximum file size in MB
        
    Returns:
        Validation result dictionary
        
    Raises:
        ValueError: If validation fails
    """
    result = {
        "valid": True,
        "errors": [],
        "sanitized_filename": filename
    }
    
    # Validate filename
    if not filename:
        result["valid"] = False
        result["errors"].append("Filename is required")
        return result
    
    # Sanitize filename
    from src.core.security import sanitize_filename
    result["sanitized_filename"] = sanitize_filename(filename)
    
    # Check file extension
    if allowed_extensions:
        file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
        if file_ext not in [ext.lower() for ext in allowed_extensions]:
            result["valid"] = False
            result["errors"].append(f"File extension '{file_ext}' not allowed")
    
    # Check file size
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        result["valid"] = False
        result["errors"].append(f"File size exceeds {max_size_mb}MB limit")
    
    # Validate content type
    if content_type:
        # Basic content type validation
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_]*\/[a-zA-Z0-9][a-zA-Z0-9!#$&\-\^_]*$', content_type):
            result["valid"] = False
            result["errors"].append("Invalid content type format")
    
    return result


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate JSON data against a schema
    
    Args:
        data: JSON data to validate
        schema: JSON schema
        
    Returns:
        True if valid, False otherwise
    """
    try:
        import jsonschema
        jsonschema.validate(data, schema)
        return True
    except Exception:
        return False


def sanitize_html(html_content: str) -> str:
    """
    Sanitize HTML content to prevent XSS attacks
    
    Args:
        html_content: HTML content to sanitize
        
    Returns:
        Sanitized HTML content
    """
    try:
        import bleach
        
        # Define allowed tags and attributes
        allowed_tags = [
            'p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li',
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote',
            'code', 'pre', 'a', 'img'
        ]
        
        allowed_attributes = {
            'a': ['href', 'title'],
            'img': ['src', 'alt', 'title', 'width', 'height'],
        }
        
        return bleach.clean(
            html_content,
            tags=allowed_tags,
            attributes=allowed_attributes,
            strip=True
        )
    except ImportError:
        # If bleach is not available, strip all HTML tags
        import re
        return re.sub(r'<[^>]+>', '', html_content)
