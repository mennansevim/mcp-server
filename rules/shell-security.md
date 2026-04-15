# Security Rules for Shell
## Priority: CRITICAL to HIGH
**Security vulnerabilities can lead to data breaches, unauthorized access, and system compromise**

---

## Injection Attacks

### Command Injection
❌ **CRITICAL:** Never use string concatenation/interpolation for system commands

**Bad:**
```bash
command="echo $user_input"
eval "$command"
```

**Good:**
```bash
echo "$user_input"
```

### SQL Injection
❌ **CRITICAL:** Never use string concatenation/interpolation for SQL queries

**Bad:**
```bash
query="SELECT * FROM Users WHERE username='$username'"
mysql -e "$query"
```

**Good:**
```bash
query="SELECT * FROM Users WHERE username=?"
mysql -e "$query" --user="$username"
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
```bash
# Bad
trap 'echo "Error: $BASH_COMMAND"' ERR

# Good
trap 'echo "An error occurred. Please try again."' ERR
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
- ❌ **HIGH:** Don't use `$RANDOM` for security-sensitive operations
- ✅ Use `/dev/urandom` or `openssl rand`

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

## Shell Specific

### Unsafe Shell Commands
❌ **CRITICAL:** Avoid using `eval` or `shell` commands with user input

**Bad:**
```bash
eval "echo $user_input"
```

**Good:**
```bash
echo "$user_input"
```

### Insecure File Permissions
❌ **HIGH:** Don't use world-writable permissions

**Bad:**
```bash
chmod 777 /path/to/file
```

**Good:**
```bash
chmod 600 /path/to/file
```

---

## Common Vulnerabilities Checklist

- [ ] Command Injection prevented (parameterized commands)
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
| Command Injection | **CRITICAL** |
| SQL Injection | **CRITICAL** |
| Hardcoded password/key | **CRITICAL** |
| Unsafe deserialization | **CRITICAL** |
| XSS vulnerability | **HIGH** |
| Missing authentication | **HIGH** |
| Weak cryptography | **HIGH** |
| Information disclosure | **MEDIUM** |
| Missing input validation | **MEDIUM** |