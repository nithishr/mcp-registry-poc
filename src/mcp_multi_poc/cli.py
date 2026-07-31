import click


@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """PoC package exposing multiple MCP servers from one PyPI distribution."""
    if ctx.invoked_subcommand is None:
        # Backward-compat behavior: bare `mcp-multi-poc` runs the default server,
        # mirroring how `couchbase-mcp-server` must keep running the operational server.
        from mcp_multi_poc.alpha_server import run

        run()


@cli.command()
def alpha() -> None:
    """Run the alpha MCP server (base dependencies only)."""
    from mcp_multi_poc.alpha_server import run

    run()


@cli.command()
def beta() -> None:
    """Run the beta MCP server (requires the [beta] extra)."""
    from mcp_multi_poc.beta_server import run

    run()
