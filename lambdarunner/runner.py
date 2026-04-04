"""Core runner: execute Lambda handlers with timeout."""

import json
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeoutError
from pathlib import Path
from typing import Any

from lambdarunner.context import LambdaContext
from lambdarunner.loader import load_handler


class LambdaTimeoutError(Exception):
    """Raised when a Lambda handler exceeds its configured timeout."""

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout
        super().__init__(f"Function timed out after {timeout} seconds")


def parse_event(event_input: str) -> dict[str, Any]:
    """Parse event from a JSON file path or inline JSON string.

    Args:
        event_input: Path to a .json file, or a raw JSON string.

    Returns:
        Parsed event dict.
    """
    if not event_input or event_input == "{}":
        return {}

    path = Path(event_input)
    if path.exists() and path.is_file():
        return json.loads(path.read_text())

    return json.loads(event_input)


def invoke(
    handler_path: str,
    event: dict[str, Any],
    timeout: int = 30,
    region: str = "us-east-1",
) -> tuple[Any, float]:
    """Invoke a Lambda handler locally.

    Args:
        handler_path: Dotted path to the handler (e.g. 'module.function').
        event: The event dict to pass to the handler.
        timeout: Timeout in seconds.
        region: Simulated AWS region.

    Returns:
        Tuple of (handler result, execution time in seconds).

    Raises:
        LambdaTimeoutError: If the handler exceeds the timeout.
    """
    handler = load_handler(handler_path)

    function_name = handler_path.rsplit(".", 1)[0].replace(".", "_")
    context = LambdaContext(
        function_name=function_name,
        timeout=timeout,
        region=region,
    )

    start = time.monotonic()

    with ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(handler, event, context)
        try:
            result = future.result(timeout=timeout)
        except FuturesTimeoutError:
            raise LambdaTimeoutError(timeout) from None

    elapsed = time.monotonic() - start
    return result, elapsed
