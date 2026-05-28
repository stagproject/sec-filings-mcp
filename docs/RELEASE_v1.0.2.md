# v1.0.2 — Discovery & registry hardening

## Changes

- **server.json:** schema `2025-12-11`, `title`, dual `remotes` (xpay + Cloud Run), xpay `key` header metadata
- **Agent Card:** v1.0.2, discovery block in `mcp` metadata
- **docs/DISCOVERY.md:** canonical URL map for registries and A2A clients

## Republish MCP Registry

```powershell
mcp-publisher login github
mcp-publisher publish
```

## Deploy

Cloud Run serves updated `agent-card.json` after next deploy (or current revision if files baked in image — redeploy if needed):

```powershell
gcloud run deploy sec-filings-mcp --source . --region us-central1 --allow-unauthenticated --port 8080
```
