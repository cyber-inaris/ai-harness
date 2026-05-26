# Secrets

This directory is reserved for local or encrypted secrets.

Do not commit real API keys, reseller account credentials, cookies, session tokens, payment details, or recovery data.

Recommended options:

- Local `.env` files ignored by git.
- `sops` + `age` encrypted files.
- Server-local files with `chmod 600`.
- Vault, Infisical, Doppler, or cloud secret managers later.

