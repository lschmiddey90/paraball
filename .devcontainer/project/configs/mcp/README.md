# Custom MCP Server Configs

Project-specific MCP server definitions. Files placed here are merged with base configs at runtime, and a project file with the same name **wins** over the base version (resolution order: `project/configs/mcp/` > `company/configs/mcp/` > `base/features/mcp-servers/configs/`).

## Adding a Server

Drop a JSON file here named after the server (e.g. `my-server.json`). The schema below is the same one used by the base configs; see `.devcontainer/base/features/mcp-servers/configs/` for full working examples (`serena.json`, `context7.json`, `playwright.json`, `chrome-devtools.json`).

After adding a file, run `make dev-configure-mcp` (or `make dev-claude mcp`) to make it selectable in the profile UI.

## Schema

```json
{
  "display_name": "My Server MCP",
  "description": "What this server does",
  "repository": {
    "url": "https://github.com/org/repo.git",
    "public": true,
    "default_branch": "main",
    "deploy_token_file": null
  },
  "build": {
    "type": "rust|python|node|npx|binary",
    "directory": "/opt/mcp-servers/my-server",
    "commands": {
      "install": "cargo build --release",
      "update": "cargo build --release"
    },
    "binary_path": "target/release/my-server",
    "build_time_minutes": 5
  },
  "token": {
    "required": true,
    "env_var": "MY_SERVER_TOKEN",
    "prefix": null,
    "prompt_instructions": "Instructions shown during token setup"
  },
  "env_vars": {
    "MY_SERVER_URL": "https://example.com"
  },
  "dependencies": [
    {
      "url": "https://example.com/org/shared-lib.git",
      "deploy_token_file": "/path/to/shared-lib.token"
    }
  ]
}
```

For the full reference (token scopes, profile system, `requires_browser`, build types, deploy tokens), see [`.devcontainer/base/features/mcp-servers/README.md`](../../../base/features/mcp-servers/README.md).
