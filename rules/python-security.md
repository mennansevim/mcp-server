# Security Rules
## Priority: CRITICAL to HIGH
**Security vulnerabilities can lead to data breaches, unauthorized access, and system compromise**

---

## Injection Attacks

### SQL Injection
❌ **CRITICAL:** Never use string concatenation/interpolation for SQL queries

**Bad:**
```python
import sqlite3
username = "admin"
query = "SELECT * FROM Users WHERE username='" + username + "'"
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute(query)
```

**Good:**
```python
import sqlite3
username = "admin"
query = "SELECT * FROM Users WHERE username=?"
conn = sqlite3.connect("database.db")
cursor = conn.cursor()
cursor.execute(query, (username,))
```

### Command Injection
❌ **CRITICAL:** Never pass user input directly to system commands

**Bad:**
```python
import os
user_input = "example.com"
os.system(f"ping {user_input}")
```

**Good:**
```python
import subprocess
user_input = "example.com"
subprocess.run(["ping", user_input], check=True, timeout=5)
```

### XSS (Cross-Site Scripting)
❌ **HIGH:** Never render unsanitized user input in HTML

**Bad:**
```python
from flask import Flask, request
app = Flask(__name__)

@app.route("/")
def index():
    user_input = request.args.get("name")
    return f"<h1>Hello, {user_input}!</h1>"
```

**Good:**
```python
from flask import Flask, request, escape
app = Flask(__name__)

@app.route("/")
def index():
    user_input = request.args.get("name")
    return f"<h1>Hello, {escape(user_input)}!</h1>"
```

---

## Authentication & Authorization

### Password Security
- ❌ **CRITICAL:** Never store passwords in plain text
- ❌ **CRITICAL:** Don't log passwords or tokens
- ✅ Always use bcrypt, Argon2, or PBKDF2
- ✅ Minimum password length: 8 characters

### Token Management
- ❌ **HIGH:** Don't expose API keys or tokens in code
- ❌ **HIGH:** Don't commit secrets to git
- ✅ Use environment variables or secret management
- ✅ Rotate tokens regularly

### Session Management
- ❌ **HIGH:** Don't use predictable session IDs
- ✅ Use secure, random session tokens
- ✅ Implement session timeout
- ✅ Regenerate session ID after login

---

## Data Exposure

### Sensitive Information
❌ **CRITICAL:** Don't log or expose:
- Passwords
- API keys
- Personal Identifiable Information (PII)
- Credit card numbers
- Social security numbers

### Error Messages
❌ **MEDIUM:** Don't expose stack traces to users
```python
# Bad
try:
    # some code
except Exception as e:
    return str(e)

# Good
import logging
try:
    # some code
except Exception as e:
    logging.error(e)
    return "An error occurred. Please try again."
```

---

## Input Validation

### General Rules
- ✅ **ALWAYS** validate all user inputs
- ✅ Whitelist acceptable values when possible
- ✅ Sanitize inputs before processing
- ✅ Validate on both client and server side

### File Upload
❌ **HIGH:** Unrestricted file upload is dangerous

**Check:**
- File type (MIME type AND extension)
- File size limits
- Scan for malware
- Store outside web root

---

## Cryptography

### Encryption
- ❌ **CRITICAL:** Don't use weak algorithms (MD5, SHA1 for passwords)
- ❌ **CRITICAL:** Don't implement custom crypto
- ✅ Use AES-256 for symmetric encryption
- ✅ Use RSA-2048+ for asymmetric encryption

### Random Numbers
- ❌ **HIGH:** Don't use `random` for security-sensitive operations
- ✅ Use `secrets` module

---

## API Security

### REST API
- ✅ Use HTTPS only
- ✅ Implement rate limiting
- ✅ Validate Content-Type headers
- ✅ Use CORS properly
- ❌ **HIGH:** Don't trust client-side validation

### Authentication
- ✅ Use OAuth 2.0 or JWT
- ✅ Implement token expiration
- ✅ Use refresh tokens properly
- ❌ **HIGH:** Don't store JWTs in localStorage (XSS risk)

---

## Database Security

### ORM Usage
- ✅ **PREFERRED:** Use parameterized queries or ORM
- ❌ **CRITICAL:** Avoid raw SQL with user input

### Access Control
- ✅ Use principle of least privilege
- ✅ Separate read/write database users
- ❌ **HIGH:** Don't use `sa` or `root` accounts

---

## Python Specific

### Deserialization
❌ **CRITICAL:** Unsafe deserialization can lead to RCE

**Bad:**
```python
import pickle
data = b"..."
obj = pickle.loads(data)  # DANGEROUS
```

**Good:**
```python
import json
data = b"..."
obj = json.loads(data.decode("utf-8"))
```

### XML External Entities (XXE)
```python
# Safe
import xml.etree.ElementTree as ET
tree = ET.parse("example.xml")
root = tree.getroot()
```

---

## Common Vulnerabilities Checklist

- [ ] SQL Injection prevented (parameterized queries)
- [ ] XSS prevented (output encoding)
- [ ] CSRF protection implemented
- [ ] Authentication required for sensitive operations
- [ ] Authorization checks in place
- [ ] Sensitive data encrypted at rest
- [ ] HTTPS enforced
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] Error messages don't expose internals
- [ ] Secrets not hardcoded or logged
- [ ] File uploads validated and restricted

---

## Severity Guidelines

| Issue | Severity |
|-------|----------|
| SQL Injection | **CRITICAL** |
| Command Injection | **CRITICAL** |
| Hardcoded password/key | **CRITICAL** |
| Unsafe deserialization | **CRITICAL** |
| XSS vulnerability | **HIGH** |
| Missing authentication | **HIGH** |
| Weak cryptography | **HIGH** |
| Information disclosure | **MEDIUM** |
| Missing input validation | **MEDIUM** |