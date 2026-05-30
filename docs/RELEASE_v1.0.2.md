# v1.0.2 — Discovery & registry hardening

## Changes

- **server.json:** schema `2025-12-11`, `title`, dual `remotes` (xpay + Cloud Run), xpay `key` header metadata
- **Agent Card:** v1.0.2, discovery block in `mcp` metadata
- **docs/DISCOVERY.md:** canonical URL map for registries and A2A clients

## Republish MCP Registry

**v1.0.2** was published via GitHub Actions on tag `v1.0.2` (workflow `publish-mcp.yml`). No local CLI required for that release.

For the next bump, either push a new tag `v*` (OIDC, no browser) or use the CLI in repo root:

```powershell
# One-time: download CLI (Windows has no global `mcp-publisher` by default)
curl.exe -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_windows_amd64.tar.gz" -o mcp-publisher.tar.gz
tar -xzf mcp-publisher.tar.gz mcp-publisher.exe
Remove-Item mcp-publisher.tar.gz

cd c:\AGS\mcp-server-finance
.\mcp-publisher.exe login github
.\mcp-publisher.exe publish
```

## Deploy

Cloud Run serves updated `agent-card.json` after next deploy (or current revision if files baked in image — redeploy if needed):

```powershell
gcloud run deploy sec-filings-mcp --source . --region us-central1 --allow-unauthenticated --port 8080
```
