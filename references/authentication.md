# GitHub Authentication

Use this reference before taking over GitHub operations for a user. Never ask the user to paste a real token into chat, logs, issues, commits, or pull requests.

## Token Safety Rules

- Do not accept tokens pasted into chat. Ask the user to save the token locally instead.
- Do not paste the token into this chat.
- Do not write real tokens to `config/auth.example.json`.
- Do not commit `config/auth.local.json`, `config/token`, or `config/*.secret.json`.
- Redact token-like values in all output as `<redacted-token>`.
- Treat classic PATs with `repo` scope as high-risk credentials. Recommend a 90-day expiry and rotate immediately if exposed.

## User-Facing Onboarding Template

Use this template when authentication is missing or unknown:

Step 1: Create a Personal Access Token
- Open https://github.com/settings/tokens.
- Choose **Generate new token (classic)**.
- Use a clear note, set expiration to **90 days**, and select **`repo`**.
- Generate the token and keep it local. Do not paste the token into this chat.

Step 2: Save the token in this skill config folder

```bash
cd <skill-path>
cp config/auth.example.json config/auth.local.json
read -rsp "Paste token (input hidden): " GITHUB_TOKEN_VALUE
printf "%s" "$GITHUB_TOKEN_VALUE" > config/token
unset GITHUB_TOKEN_VALUE
chmod 600 config/token
```

Step 3: Connect the token to gh

```bash
gh auth login --with-token < config/token
gh auth setup-git
```

Step 4: Verify authentication

```bash
gh auth status
```

After Step 4 succeeds, continue with repository inspection before any mutation.

## Create Personal Access Token

1. Visit https://github.com/settings/tokens.
2. Click **Generate new token (classic)**.
3. Fill **Note** with a recognizable name, such as `OpenClaw Homepage`.
4. Set expiration to **90 days**.
5. Select scope **`repo`** for full repository control.
6. Click **Generate token**.
7. Copy the token once. It usually starts with `ghp_`.

## Save Token In Skill Config

Run these commands from the skill folder:

```bash
cd <skill-path>
cp config/auth.example.json config/auth.local.json
read -rsp "Paste token (input hidden): " GITHUB_TOKEN_VALUE
printf "%s" "$GITHUB_TOKEN_VALUE" > config/token
unset GITHUB_TOKEN_VALUE
chmod 600 config/token
```

On Windows PowerShell:

```powershell
Set-Location <skill-path>
Copy-Item config/auth.example.json config/auth.local.json
$secureToken = Read-Host "Paste token" -AsSecureString
$tokenPtr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureToken)
try {
    $plainToken = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($tokenPtr)
    Set-Content -NoNewline -Path config/token -Value $plainToken
}
finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($tokenPtr)
    Remove-Variable secureToken, plainToken -ErrorAction SilentlyContinue
}
```

The tracked reference config is `config/auth.example.json`. The local private config is `config/auth.local.json`.

## Use Token With gh

Authenticate `gh` from the skill folder:

```bash
gh auth login --with-token < config/token
gh auth setup-git
gh auth status
```

If `config/auth.local.json` changes `token_env`, load the token through that environment variable instead of a file.

## Use Token For Push

Manual push:

```bash
git push
# Username: your GitHub username
# Password: paste the token when prompted; it will not display
```

Helper push:

```bash
~/github-push.sh /path/to/repo main
```

After authentication, verify the target repository before push, merge, release, or settings changes.
