"""CLI entry point using Typer + Rich."""

import json
import sys
from typing import Annotated

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from lambdarunner.loader import load_env_file
from lambdarunner.runner import LambdaTimeoutError, invoke, parse_event

app = typer.Typer(
    name="lambdarunner",
    help="Run AWS Lambda handlers locally. No Docker, no SAM, no AWS.",
    no_args_is_help=True,
    invoke_without_command=True,
)
console = Console()
err_console = Console(stderr=True)


@app.callback()
def main() -> None:
    """Run AWS Lambda handlers locally. No Docker, no SAM, no AWS."""


@app.command("invoke")
def invoke_cmd(
    handler: Annotated[
        str,
        typer.Argument(help="Handler path in module.function format"),
    ],
    event: Annotated[
        str,
        typer.Option(
            "--event",
            "-e",
            help="Path to JSON file or inline JSON string",
        ),
    ] = "{}",
    timeout: Annotated[
        int,
        typer.Option("--timeout", "-t", help="Timeout in seconds"),
    ] = 30,
    env_file: Annotated[
        str | None,
        typer.Option("--env-file", help="Path to .env file"),
    ] = None,
    region: Annotated[
        str,
        typer.Option("--region", help="Simulated AWS region"),
    ] = "us-east-1",
    profile: Annotated[
        str | None,
        typer.Option("--profile", help="AWS profile name for context"),
    ] = None,
    pretty: Annotated[
        bool,
        typer.Option("--pretty/--no-pretty", help="Pretty print JSON output"),
    ] = True,
) -> None:
    """Invoke a Lambda handler locally."""
    # Display invocation info
    event_display = event if event != "{}" else "(empty)"
    info_text = (
        f"[bold]Handler[/bold]  : {handler}\n"
        f"[bold]Event[/bold]    : {event_display}\n"
        f"[bold]Timeout[/bold]  : {timeout}s\n"
        f"[bold]Region[/bold]   : {region}"
    )
    if profile:
        info_text += f"\n[bold]Profile[/bold]  : {profile}"

    console.print(Panel(info_text, title="Lambda Runner", border_style="cyan"))

    # Load env file if provided
    if env_file:
        try:
            loaded = load_env_file(env_file)
            console.print(
                f"[dim]Loaded {len(loaded)} env variable(s) from {env_file}[/dim]"
            )
        except FileNotFoundError as exc:
            err_console.print(
                Panel(f"[red]{exc}[/red]", title="Error", border_style="red")
            )
            raise typer.Exit(1) from None

    # Parse event
    try:
        parsed_event = parse_event(event)
    except (json.JSONDecodeError, FileNotFoundError) as exc:
        err_console.print(
            Panel(
                f"[red]Failed to parse event: {exc}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1) from None

    # Invoke
    console.print("[bold cyan]▶ Invoking...[/bold cyan]")

    try:
        result, elapsed = invoke(
            handler_path=handler,
            event=parsed_event,
            timeout=timeout,
            region=region,
        )
    except LambdaTimeoutError as exc:
        err_console.print(
            Panel(
                f"[red]LambdaTimeoutError: {exc}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1) from None
    except (ValueError, ModuleNotFoundError, AttributeError) as exc:
        err_console.print(
            Panel(
                f"[red]{type(exc).__name__}: {exc}[/red]",
                title="Error",
                border_style="red",
            )
        )
        raise typer.Exit(1) from None
    except Exception as exc:
        err_console.print(
            Panel(
                f"[red]{type(exc).__name__}: {exc}[/red]",
                title="Handler Error",
                border_style="red",
            )
        )
        if "--traceback" not in sys.argv:
            console.print("[dim]The handler raised an unhandled exception.[/dim]")
        raise typer.Exit(1) from None

    # Display result
    elapsed_ms = int(elapsed * 1000)

    if isinstance(result, (dict, list)):
        if pretty:
            formatted = json.dumps(result, indent=2, ensure_ascii=False)
            output = Syntax(formatted, "json", theme="monokai")
        else:
            output = json.dumps(result, ensure_ascii=False)
    else:
        output = str(result)

    console.print(Panel(output, title=f"Result ({elapsed_ms}ms)", border_style="green"))


if __name__ == "__main__":
    app()
