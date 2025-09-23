# Security Architecture and Patterns

## Defense-in-Depth Security Model

**ALL CODE MUST IMPLEMENT COMPREHENSIVE SECURITY CONTROLS**

The Your Morning Brief project implements a multi-layered security architecture that MUST be followed for all development.

## Layer 1: Network Security

### SSRF Protection (MANDATORY)

```python
# ✅ CORRECT: Block private IP ranges
BLOCKED_IP_RANGES = [
    "10.0.0.0/8",      # Private class A
    "172.16.0.0/12",   # Private class B
    "192.168.0.0/16",  # Private class C
    "127.0.0.0/8",     # Loopback
]

# ✅ CORRECT: Always verify SSL certificates
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED
```

### Request Security

```python
# ✅ CORRECT: Enforce size limits and timeouts
MAX_RESPONSE_SIZE_MB = 10
INGESTION_TIMEOUT_SEC = 10
MAX_REDIRECTS = 3

# ✅ CORRECT: Rate limiting implementation
@limiter.limit("10/minute")
def feed_endpoint():
    pass
```

## Layer 2: Input Validation & Sanitization

### HTML Sanitization (MANDATORY)

```python
# ✅ CORRECT: Strip ALL HTML/JavaScript
import bleach

def sanitize_content(content: str) -> str:
    """Strip all HTML/JavaScript from content."""
    return bleach.clean(content, tags=[], strip=True)

# ❌ INCORRECT: Allowing any HTML tags
return bleach.clean(content, tags=['p', 'a'])  # XSS risk
```

### URL Validation

```python
# ✅ CORRECT: Validate URL schemes and structure
def validate_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in ['http', 'https']:
        return False
    # Additional validation...
    return True
```

### Pydantic Input Validation

```python
# ✅ CORRECT: Validate ALL external inputs
class RSSSourceCreate(BaseModel):
    url: str = Field(..., min_length=1, max_length=2048)
    name: str = Field(..., min_length=1, max_length=255)

    @field_validator('url')
    def validate_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must use http or https scheme')
        return v
```

## Layer 3: Data Processing Security

### SQL Injection Prevention (MANDATORY)

```python
# ✅ CORRECT: Always use SQLAlchemy ORM with parameterized queries
def get_source_by_url(db: Session, url: str) -> Optional[Source]:
    return db.query(Source).filter(Source.url == url).first()

# ❌ INCORRECT: Never use raw SQL with string formatting
def get_source_bad(db: Session, url: str):
    query = f"SELECT * FROM sources WHERE url = '{url}'"  # SQL injection risk!
    return db.execute(query)
```

### Content Hash Security

```python
# ✅ CORRECT: Use sanitized inputs for hashing
def generate_content_hash(title: str, content: str) -> str:
    sanitized_title = bleach.clean(title, tags=[], strip=True)
    sanitized_content = bleach.clean(content, tags=[], strip=True)
    combined = f"{sanitized_title}:{sanitized_content}"
    return hashlib.sha256(combined.encode('utf-8')).hexdigest()
```

### Unicode Normalization

```python
# ✅ CORRECT: Apply NFKC normalization
import unicodedata

def normalize_text(text: str) -> str:
    return unicodedata.normalize('NFKC', text)
```

## Layer 4: Application Security

### API Key Management

```python
# ✅ CORRECT: Encrypt API keys at rest
from cryptography.fernet import Fernet

def encrypt_api_key(key: str, encryption_key: bytes) -> str:
    f = Fernet(encryption_key)
    return f.encrypt(key.encode()).decode()

def decrypt_api_key(encrypted_key: str, encryption_key: bytes) -> str:
    f = Fernet(encryption_key)
    return f.decrypt(encrypted_key.encode()).decode()
```

### Secure Error Handling

```python
# ✅ CORRECT: Mask sensitive data in logs
def log_error_safely(error: Exception, context: dict):
    safe_context = {k: v for k, v in context.items()
                   if k not in ['api_key', 'password', 'token']}
    logger.error(f"Error: {type(error).__name__}", extra=safe_context)

# ❌ INCORRECT: Logging sensitive data
logger.error(f"API call failed with key: {api_key}")  # Leaks API key!
```

### Rate Limiting and Cost Controls

```python
# ✅ CORRECT: Multi-layered budgets with circuit breakers
class CostController:
    def __init__(self):
        self.daily_request_limit = 1000
        self.daily_token_budget = 50000
        self.daily_cost_limit_usd = 10.0

    def check_budget(self, estimated_cost: float) -> bool:
        return self.current_cost + estimated_cost <= self.daily_cost_limit_usd
```

## Security Testing Requirements

### Required Security Tests

ALL code must include these security test patterns:

```python
# XSS payload injection tests
def test_xss_protection():
    malicious_content = "<script>alert('xss')</script>"
    sanitized = sanitize_content(malicious_content)
    assert "<script>" not in sanitized
    assert "alert" not in sanitized

# SQL injection attempt validation
def test_sql_injection_protection():
    malicious_input = "'; DROP TABLE sources; --"
    source = get_source_by_url(db, malicious_input)
    # Should not find anything and should not crash

# SSRF attack simulation
def test_ssrf_protection():
    malicious_url = "http://127.0.0.1:8080/admin"
    with pytest.raises(SecurityError):
        validate_url_security(malicious_url)
```

## Environment Security Variables

### Required Security Configuration

```bash
# API Security
OPENAI_API_KEY_ENCRYPTED=<encrypted_key>
API_KEY_ENCRYPTION_KEY_PATH=/app/secrets/encryption.key

# Rate Limiting
DAILY_REQUEST_LIMIT=1000
DAILY_TOKEN_BUDGET=50000
DAILY_COST_LIMIT_USD=10.0

# Network Security
SSL_VERIFY=true
MAX_RESPONSE_SIZE_MB=10
INGESTION_TIMEOUT_SEC=10

# Database Security
DATABASE_SSL_MODE=require
DATABASE_CONNECTION_TIMEOUT=30
```

## Security Monitoring and Logging

### Required Security Event Logging

```python
# ✅ CORRECT: Log security events with classification
def log_security_event(event_type: str, details: dict):
    logger.warning(
        f"SECURITY_EVENT: {event_type}",
        extra={
            "security_event": True,
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
    )

# Examples of events to log:
# - Failed authentication attempts
# - Rate limit violations
# - SSRF attempt blocks
# - XSS sanitization events
# - API cost overruns
# - Unusual error patterns
```

### Log Security Rules

- **NEVER** log API keys, passwords, or sensitive content
- **ALWAYS** truncate content logs to 200 characters maximum
- **ALWAYS** use structured logging with security event classification
- **ALWAYS** implement log rotation and secure storage

## Common Security Patterns

### Feed Processing Security

```python
# ✅ CORRECT: Comprehensive feed processing security
async def process_feed_securely(feed_url: str) -> ProcessingResult:
    # 1. Validate URL
    if not validate_url_security(feed_url):
        raise SecurityError("URL failed security validation")

    # 2. Apply rate limiting
    await rate_limiter.acquire()

    # 3. Fetch with security controls
    content = await fetch_with_security(feed_url)

    # 4. Sanitize all content
    sanitized_entries = [sanitize_feed_entry(entry) for entry in content.entries]

    # 5. Validate and normalize
    validated_entries = [validate_entry(entry) for entry in sanitized_entries]

    return ProcessingResult(entries=validated_entries)
```

## Security Compliance Standards

- **OWASP Top 10** compliance for web applications
- **OWASP API Security Top 10** for API endpoints
- **Secure coding practices** per SANS/CWE guidelines
- **Data protection** considerations for RSS content processing

## Security Review Process

- Security review REQUIRED for all milestone implementations
- Automated security scanning in CI/CD pipeline
- Manual security testing before production deployment
- Regular security audits and penetration testing
