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
| 5 | Is there any schema-legal way to run a console script **named differently than the package** (`mcp-multi-poc-beta`)? | `server.beta-script.json`. 5a (failed): identifier = script name → 404, identifier must be a real PyPI package. 5b (current file): identifier = real package, script name smuggled as a **positional `runtimeArgument`** → `uvx --from 'mcp-multi-poc[beta]' mcp-multi-poc-beta mcp-multi-poc`; the appended identifier becomes a stray arg the server must ignore. If 5b also fails, fallback is a **shim package** per script |

## Findings so far (2026-07-31)

- **Q1 — multiple entries per PyPI package: YES.** `mcp-multi-poc-alpha` published
  against the shared package.
- **Q2 — multiple `mcp-name` comments in one README: YES** (alpha validated with
  three comments present).
- **Q3 — extras in `identifier`: NO, but expressible via `runtimeArguments`.**
  Extras in the identifier fail the literal PyPI lookup —
  `PyPI package 'mcp-multi-poc[beta]' not found (status: 404)`. Fallback
  **works**: `mcp-multi-poc-beta` published successfully with plain
  `identifier: mcp-multi-poc` + `runtimeArguments: --from "mcp-multi-poc[beta]"`
  (live in the registry, verified via the `/v0/servers` API).
- **Q5a — differently-named console script as identifier: NO (confirmed on
  publish).** Same 404 mechanism (`'mcp-multi-poc-beta' not found`) — the
  registry validates the identifier as a real PyPI package before anything else.
- **Q5b — script name as positional `runtimeArgument`: YES, published.**
  `io.github.nithishr/mcp-multi-poc-beta-script` is live (published
  2026-07-31, after trimming `description` to the 100-char limit — the only
  validation hiccup). Locally, `uvx --from 'mcp-multi-poc[beta]'
  mcp-multi-poc-beta mcp-multi-poc` completes the MCP initialize handshake —
  the trailing identifier is silently ignored because `main()` never parses
  argv. Caveats: only safe when the entrypoint tolerates stray argv (click
  needs `ignore_unknown_options` + `allow_extra_args` or a dummy optional
  argument); depends on clients preserving `runtimeArguments` order — the
  least-exercised metadata path; registry UIs show the identifier as the
  runnable. For production script-per-server, prefer a **shim package** per
  script (identifier == script name, no runtimeArguments at all).
- **Registry validation limits discovered:** `description` ≤ 100 chars;
  `identifier` must be a literal, existing PyPI package (extras rejected);
  `runtimeArguments`/`packageArguments` contents are NOT validated.

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

## Q4 — testing the published entries from a client

Most clients don't install directly from the official registry yet, so Q4
splits in two: (a) does the spec-mandated command construction
(`uvx <runtimeArguments> <identifier> <packageArguments>`) produce a working
server, and (b) does a registry-consuming client reproduce that construction.

1. **Fetch what was actually published** and check the `packages` block:
   `curl "https://registry.modelcontextprotocol.io/v0/servers?search=mcp-multi-poc"`
2. **MCP Inspector** — interactive tool calls against the hand-assembled command:
   ```bash
   npx @modelcontextprotocol/inspector uvx mcp-multi-poc alpha
   npx @modelcontextprotocol/inspector uvx --from "mcp-multi-poc[beta]" mcp-multi-poc beta
   ```
3. **Claude Code** — same commands as stdio servers, then call `echo` / `make_table`:
   ```bash
   claude mcp add poc-alpha -- uvx mcp-multi-poc alpha
   claude mcp add poc-beta -- uvx --from "mcp-multi-poc[beta]" mcp-multi-poc beta
   ```
   (For Claude Desktop, the equivalent `claude_desktop_config.json` entries:)
   ```json
   {
     "mcpServers": {
       "poc-alpha": { "command": "uvx", "args": ["mcp-multi-poc", "alpha"] },
       "poc-beta":  { "command": "uvx", "args": ["--from", "mcp-multi-poc[beta]", "mcp-multi-poc", "beta"] }
     }
   }
   ```
4. **Registry-native install (the real (b) test)**: VS Code's MCP server
   gallery is backed by the official registry — search for `mcp-multi-poc`
   there and install; this exercises whether a client assembles
   `runtimeArguments + identifier + packageArguments` on its own. Entries may
   lag or be curated before appearing.

Steps 2–3 only prove (a); only step 4 (or another registry-consuming client)
proves (b), which is what the beta/beta-script entries actually depend on.
