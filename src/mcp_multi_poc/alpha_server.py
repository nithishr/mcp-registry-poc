from fastmcp import FastMCP

mcp = FastMCP("poc-alpha")


@mcp.tool
def echo(text: str) -> str:
    """Echo the input text back."""
    return f"alpha: {text}"


def run() -> None:
    mcp.run()
