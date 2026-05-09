# Security Policy

## Supported Versions

The current supported version is `0.1.0`.

## Reporting a Vulnerability

Do not open public issues for credential exposure, token handling bugs, or vulnerabilities that could affect private repositories.

Contact Jiyuan Liu at <erie@seu.edu.cn> with a concise report, reproduction steps, affected files, and any relevant logs with secrets redacted.

## Credential Handling

Never commit:

- `config/auth.local.json`
- `config/token`
- `config/*.secret.json`
- real GitHub tokens
- private repository exports or sensitive audit reports

Use `references/authentication.md` for local token setup guidance.
