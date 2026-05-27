# MCP Registry — publish `io.github.stagproject/sec-filings-mcp`

Official registry: https://registry.modelcontextprotocol.io

## One-time setup (maintainer)

Requires interactive GitHub login once per machine (`mcp-publisher login github` opens the browser).

```powershell
# Install publisher CLI (Windows)
curl.exe -L "https://github.com/modelcontextprotocol/registry/releases/latest/download/mcp-publisher_windows_amd64.tar.gz" -o mcp-publisher.tar.gz
tar -xzf mcp-publisher.tar.gz mcp-publisher.exe

# From repo root
cd c:\AGS\mcp-server-finance
.\mcp-publisher.exe login github
.\mcp-publisher.exe publish --dry-run
.\mcp-publisher.exe publish
```

**Or** push tag `v1.0.1` — workflow `.github/workflows/publish-mcp.yml` uses `login github-oidc` (repo must allow OIDC to MCP Registry).

## Verify

```powershell
curl.exe "https://registry.modelcontextprotocol.io/v0/servers?search=io.github.stagproject/sec-filings-mcp"
```

## Automated publish

On git tag `v*` (e.g. `v1.0.1`), GitHub Actions workflow `.github/workflows/publish-mcp.yml` publishes via OIDC.

## server.json

Configured at repo root — remote URL:

`https://sec-edgar-filings.mcp.xpay.sh/mcp`
