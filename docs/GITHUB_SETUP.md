# GitHub Setup

## 1. Create Remote Repo
Create an empty repository on GitHub, then run:

```bash
git remote add origin <YOUR_GITHUB_REPO_URL>
git add .
git commit -m "Initial intelligent trade surveillance scaffold"
git push -u origin main
```

## 2. Configure GitHub Secrets (for optional deploy/publish)
- Any cloud deploy credentials you choose
- Optional market data API keys

The included workflows already run tests/builds on push and can publish images to GHCR manually.
