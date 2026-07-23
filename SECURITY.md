# Security policy

This repository is an interview and learning project. Before production use:

- Replace the JWT secret and store it in a secret manager.
- Use HTTPS only.
- Add refresh-token rotation and account verification.
- Use a managed identity provider where appropriate.
- Verify payment webhook signatures.
- Add rate limiting and abuse protection.
- Avoid logging authentication tokens and payment data.
- Run dependency and container security scans.
- Apply least-privilege database credentials.
