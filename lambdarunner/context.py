"""Fake AWS Lambda Context object."""

import time
import uuid


class LambdaContext:
    """Simulates the AWS Lambda context object injected into handlers."""

    def __init__(
        self,
        function_name: str = "test_function",
        timeout: int = 30,
        memory_limit_in_mb: int = 128,
        region: str = "us-east-1",
    ) -> None:
        self.function_name = function_name
        self.function_version = "$LATEST"
        self.memory_limit_in_mb = memory_limit_in_mb
        self.aws_request_id = str(uuid.uuid4())
        self.log_group_name = f"/aws/lambda/{function_name}"
        self.log_stream_name = (
            f"{time.strftime('%Y/%m/%d')}/[$LATEST]{uuid.uuid4().hex}"
        )
        self.invoked_function_arn = (
            f"arn:aws:lambda:{region}:123456789012:function:{function_name}"
        )
        self._timeout = timeout
        self._start_time = time.monotonic()

    def get_remaining_time_in_millis(self) -> int:
        """Return milliseconds remaining before timeout."""
        elapsed = time.monotonic() - self._start_time
        remaining = (self._timeout - elapsed) * 1000
        return max(0, int(remaining))

    def __str__(self) -> str:
        return (
            f"LambdaContext("
            f"function_name={self.function_name!r}, "
            f"aws_request_id={self.aws_request_id!r}, "
            f"memory_limit_in_mb={self.memory_limit_in_mb}, "
            f"remaining_time={self.get_remaining_time_in_millis()}ms"
            f")"
        )
