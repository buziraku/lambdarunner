"""Sample Lambda handlers for testing."""

import time


def lambda_handler(event, context):
    """Simple handler that returns event data."""
    return {
        "statusCode": 200,
        "body": f"Hello {event.get('name', 'World')}",
        "requestId": context.aws_request_id,
    }


def error_handler(event, context):
    """Handler that always raises an exception."""
    raise RuntimeError("Something went wrong in the handler")


def slow_handler(event, context):
    """Handler that sleeps longer than any reasonable timeout."""
    time.sleep(60)
    return {"statusCode": 200}
