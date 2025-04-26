# Security Considerations for FTP Credential Management

## Overview

This document outlines security considerations and best practices for the FTP credential management system. Security is a critical aspect of credential storage and management, especially when dealing with credentials that grant access to production websites. Special attention is given to containerization security considerations.

## Key Security Principles

1. **Least Privilege**
   - Store only the credentials that are absolutely necessary
   - Use restricted FTP accounts with minimal permissions
   - Regularly audit and rotate credentials

2. **Defense in Depth**
   - Multiple layers of security protection
   - No single point of failure
   - Assume breach mentality in design

3. **Secure by Default**
   - Secure configuration out of the box
   - No insecure fallbacks
   - Clear security documentation

## Backend-Specific Security Considerations

### File Backend Security

1. **File Protection**
   - Restrictive file permissions (600) for credential files
   - Store in user home directory or protected application data folder
   - Add to .gitignore to prevent accidental commits

2. **Encryption**
   - Use Fernet symmetric encryption from cryptography package
   - AES-128-CBC with proper PKCS7 padding
   - Secure random IV generation for each encryption operation

3. **Key Management**
   - Key derivation from master password or system-specific value
   - Key storage in system keyring or secure environment variable
   - Multiple encryption layers for critical values

### Environment Backend Security

1. **Environment Variable Protection**
   - Set environment variables at runtime, not in scripts
   - Use process-level environment variables rather than system-wide
   - Avoid printing environment variables or logging them

2. **Container Considerations**
   - Don't store credentials in Dockerfiles (use build args instead)
   - Use Docker secrets or Kubernetes secrets when available
   - Consider credential injection patterns at runtime

3. **Ephemeral Nature**
   - Understand environment variables don't persist across container restarts
   - Plan for credential recreation/restoration
   - Consider external storage for persistence when needed

### External API Backend Security (Vault, AWS, etc.)

1. **Authentication**
   - Use minimal-privilege access tokens
   - Enable MFA where possible
   - Rotate access tokens regularly

2. **Transport Security**
   - Always use HTTPS for API communication
   - Validate TLS certificates
   - Consider mutual TLS for high-security environments

3. **Authorization**
   - Implement proper ACLs in the secret management service
   - Audit access regularly
   - Follow principle of least privilege

## Threat Model

| Threat | Impact | Mitigation |
|--------|--------|------------|
| Unauthorized access to credentials | Complete website compromise | Encryption, access controls |
| Credentials in logs | Exposure of sensitive data | Secure logging practices |
| Key extraction from memory | Credential compromise | Secure memory handling |
| Hardcoded credentials in code | Long-term credential exposure | Credential references only |
| Man-in-the-middle during FTP | Credential interception | Consider FTPS support |
| Container image containing credentials | Credential exposure via image | Use runtime secrets injection |
| Secrets in container environment | Multi-tenant compromise | Use dedicated secret volumes |
| API token compromise | External backend access | Short-lived tokens, MFA |

## Implementation Guidelines for File Backend

```python
from cryptography.fernet import Fernet
import base64
import os
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Key derivation (done once)
def generate_key(password: str, salt: bytes = None):
    if salt is None:
        salt = os.urandom(16)
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key, salt

# Encryption
def encrypt_value(value: str, key: bytes):
    f = Fernet(key)
    return f.encrypt(value.encode())

# Decryption
def decrypt_value(encrypted_value: bytes, key: bytes):
    f = Fernet(key)
    return f.decrypt(encrypted_value).decode()
```

## Container-Specific Security Practices

### Docker

1. **Secrets Management**
   - Use Docker secrets for swarm mode:
     ```bash
     echo "MyFTPPassword" | docker secret create ftp_password -
     ```
   - Reference in compose files:
     ```yaml
     services:
       app:
         secrets:
           - ftp_password
     secrets:
       ftp_password:
         external: true
     ```

2. **Build-time vs. Runtime**
   - Never include secrets at build time
   - Use multi-stage builds to avoid leaking build args
   - Use environment files (.env) mounted at runtime

3. **Volume Security**
   - If using file backend, use volumes for credential storage
   - Set proper permissions on volumes
   - Consider tmpfs for in-memory secret storage

### Kubernetes

1. **Secrets Management**
   - Use Kubernetes secrets:
     ```yaml
     apiVersion: v1
     kind: Secret
     metadata:
       name: ftp-credentials
     type: Opaque
     data:
       username: <base64-encoded-username>
       password: <base64-encoded-password>
     ```

2. **Secret Mounting**
   - Mount as environment variables:
     ```yaml
     env:
       - name: CRED_SAMPLE_WEBSITE_FTP_USERNAME
         valueFrom:
           secretKeyRef:
             name: ftp-credentials
             key: username
     ```
   - Or mount as files:
     ```yaml
     volumes:
     - name: ftp-creds
       secret:
         secretName: ftp-credentials
     ```

3. **Additional Protection**
   - Use network policies to restrict secret access
   - Consider external secret stores (HashiCorp Vault)
   - Use RBAC to limit who can view secrets

## Secure Credential Format

### File Backend Format
```json
{
    "SITE_NAME_1": {
        "FTP_USERNAME": "<encrypted>",
        "FTP_PASSWORD": "<encrypted>"
    },
    "SITE_NAME_2": {
        "FTP_USERNAME": "<encrypted>",
        "FTP_PASSWORD": "<encrypted>"
    }
}
```

### Environment Backend Naming Convention
```
CRED_SITE_NAME_1_FTP_USERNAME=value
CRED_SITE_NAME_1_FTP_PASSWORD=value
CRED_SITE_NAME_2_FTP_USERNAME=value
CRED_SITE_NAME_2_FTP_PASSWORD=value
```

## Runtime Security

### Memory Protection
- Clear sensitive variables after use
- Avoid logging credentials even in debug mode
- Use secure string handling where available

### Example Memory Cleanup
```python
def secure_operation_with_credentials(username, password):
    try:
        # Perform operation with credentials
        result = some_operation(username, password)
        return result
    finally:
        # Explicit cleanup
        if 'username' in locals():
            username = '*' * len(username)
        if 'password' in locals():
            password = '*' * len(password)
```

## Authentication and Access Controls

### User Authentication
- Require authentication before accessing credentials
- Consider multi-factor authentication for high-value credentials
- Time-limited access to decrypted credentials

### Permission Model
- Operation-based permissions (read/write/delete)
- User-based access controls where needed
- Audit logging for credential access

## Secure Development Practices

### Code Review
- Mandatory review for all credential-handling code
- Regular security audits
- Automated scanning for security issues

### Testing
- Penetration testing of credential storage
- Fuzzing for edge cases in credential handling
- Verification of encryption implementation
- Container-specific security testing

### Documentation
- Clear security documentation for users
- Examples of secure use
- Warning labels for potential security issues
- Containerization security best practices

## Incident Response

### Detection
- Logging of credential access
- Monitoring for suspicious activity
- Alerting for unusual patterns

### Response Plan
- Credential rotation process
- Containment procedures
- Communication templates

### Recovery
- Backup/restore procedures for credential data
- Alternative authentication methods
- Post-incident analysis template

## Best Practices for Users

1. **Use Strong Credentials**
   - Unique passwords for each website
   - Password manager for generation and storage
   - Regular credential rotation

2. **Secure Environment**
   - Keep system updated with security patches
   - Use antivirus and firewall protection
   - Secure physical access to development machines

3. **Operational Security**
   - Never share credentials via insecure channels
   - Don't reuse FTP credentials for other services
   - Report suspected security incidents immediately

4. **Container Best Practices**
   - Regularly scan container images for vulnerabilities
   - Use minimal base images to reduce attack surface
   - Never use credentials in Dockerfiles or baked into images
   - Use orchestration-provided secret management features

## Security Roadmap

### Phase 1 (Current Implementation)
- Basic encryption of credential store with file backend
- Environment variable backend for containerization
- File permission controls
- Separation from configuration

### Phase 2 (Future Enhancements)
- Enhanced key management
- Support for FTPS/SFTP protocols
- Advanced audit logging
- Integration with orchestration secret management

### Phase 3 (Long-term Goals)
- Integration with external secret management services
- Zero-knowledge credential handling
- Hardware security module support
- Automated credential rotation 