import sys

from fastmcp import FastMCP

mcp = FastMCP("poc-beta")


@mcp.tool
def make_table(rows: list[list[str]]) -> str:
    """Render rows of strings as a plain-text table."""
    from tabulate import tabulate

    return tabulate(rows)


def _require_extra() -> None:
    try:
        import tabulate  # noqa: F401
    except ModuleNotFoundError:
        sys.exit(
            "The beta server requires the 'beta' extra:\n"
            '  pip install "mcp-multi-poc[beta]"\n'
            '  uvx "mcp-multi-poc[beta]" beta'
        )


def run() -> None:
    _require_extra()
    mcp.run()


def main() -> None:
    """Entry point for the mcp-multi-poc-beta console script (Option 1 test)."""
    run()
