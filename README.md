# mcp-multi-poc

PoC for serving **multiple MCP servers from a single PyPI package**, using
subcommands for server selection and optional extras for on-demand dependencies.
Stands in for the Couchbase MCP monorepo question (alpha = operational,
beta = analytics, tabulate = the analytics SDK — chosen because it is *outside*
fastmcp's transitive dependency tree; httpx and pyyaml are not, and silently
defeat the extras guard).

<!-- mcp-name: io.github.nithishr/mcp-multi-poc-alpha -->
<!-- mcp-name: io.github.nithishr/mcp-multi-poc-beta -->
<!-- mcp-name: io.github.nithishr/mcp-multi-poc-beta-script -->

## What this PoC must answer

| # | Question | Where it's tested |
| --- | --- | --- |
| 1 | Can two MCP registry entries point at the **same PyPI package**? | Publish both `server.alpha.json` and `server.beta.json` |
| 2 | Does registry ownership validation accept **multiple `mcp-name` comments** in one package README? | The two HTML comments above |
| 3 | Does the registry schema/validator accept **extras syntax in `identifier`** (`mcp-multi-poc[beta]`)? | `server.beta.json` — if rejected, fall back to plain identifier and record that extras can't be expressed |
| 4 | Do clients run the **subcommand form** correctly from registry metadata (`uvx mcp-multi-poc alpha`)? | Install both servers from a client (Claude Desktop / MCP Inspector) |
| 5 | Is there any schema-legal way to run a console script **named differently than the package** (`mcp-multi-poc-beta`)? | `server.beta-script.json`: identifier = script name + `runtimeArguments: --from mcp-multi-poc[beta]`. Expected failure mode: ownership validation rejects the identifier because `mcp-multi-poc-beta` is not a real PyPI package. If it fails, the fallback for script-per-server is a **shim package** published under the script's name |

## Local smoke test (before publishing anything)

```bash
cd mcp-registry-poc
uv venv && uv pip install -e .
mcp-multi-poc alpha          # starts alpha on stdio (Ctrl+C to exit)
mcp-multi-poc beta           # must FAIL with the friendly extras message
uv pip install -e ".[beta]"
mcp-multi-poc beta           # now starts
mcp-multi-poc                # bare command runs alpha (backward-compat check)
mcp-multi-poc-beta           # Option 1 script works locally once extra installed
```

uvx behavior (after publishing to PyPI):

```bash
uvx mcp-multi-poc alpha                  # base only
uvx "mcp-multi-poc[beta]" beta           # extras via uvx — key UX under test
uvx --from "mcp-multi-poc[beta]" mcp-multi-poc-beta   # Option 1 fallback form
```

## Publish steps (manual, in order)

1. If `mcp-multi-poc` is taken on PyPI, pick another name and rename consistently
   (pyproject `name`, `[project.scripts]`, both server.json identifiers).
3. Build and publish to **real PyPI** (registry validation fetches from pypi.org;
   TestPyPI will not work): `uv build && uv publish`.
4. Install mcp-publisher and log in:
   `mcp-publisher login github` (interactive) — must match the `io.github.<username>` namespace.
5. Publish the entries:
   `mcp-publisher publish server.alpha.json`, `... server.beta.json`, and
   `... server.beta-script.json` — the last one is *expected* to fail validation;
   record the exact error (if the CLI expects the file at `./server.json`, copy
   each into place first).
6. Verify via the registry API:
   `curl "https://registry.modelcontextprotocol.io/v0/servers?search=mcp-multi-poc"`
7. Configure both servers in a client from the registry metadata and call
   `echo` (alpha) and `make_table` (beta).
8. Record results per question above, then deprecate/delete the PoC entries.

## MCP client config for manual testing (pre-registry)

```json
{
  "mcpServers": {
    "poc-alpha": { "command": "uvx", "args": ["mcp-multi-poc", "alpha"] },
    "poc-beta":  { "command": "uvx", "args": ["mcp-multi-poc[beta]", "beta"] }
  }
}
```
