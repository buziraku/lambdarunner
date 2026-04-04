"""Tests for LambdaContext."""

import time

from lambdarunner.context import LambdaContext


def test_context_defaults():
    ctx = LambdaContext()
    assert ctx.function_name == "test_function"
    assert ctx.function_version == "$LATEST"
    assert ctx.memory_limit_in_mb == 128
    assert "arn:aws:lambda:us-east-1" in ctx.invoked_function_arn
    assert ctx.log_group_name == "/aws/lambda/test_function"
    assert len(ctx.aws_request_id) == 36  # UUID format


def test_context_custom_values():
    ctx = LambdaContext(
        function_name="my_func",
        timeout=60,
        memory_limit_in_mb=256,
        region="eu-west-1",
    )
    assert ctx.function_name == "my_func"
    assert ctx.memory_limit_in_mb == 256
    assert "eu-west-1" in ctx.invoked_function_arn


def test_remaining_time_decreases():
    ctx = LambdaContext(timeout=10)
    t1 = ctx.get_remaining_time_in_millis()
    time.sleep(0.05)
    t2 = ctx.get_remaining_time_in_millis()
    assert t2 < t1


def test_remaining_time_initial_value():
    ctx = LambdaContext(timeout=5)
    remaining = ctx.get_remaining_time_in_millis()
    # Should be close to 5000ms (allow 200ms slack for test execution)
    assert 4800 <= remaining <= 5000


def test_remaining_time_never_negative():
    ctx = LambdaContext(timeout=0)
    time.sleep(0.01)
    assert ctx.get_remaining_time_in_millis() == 0


def test_str_representation():
    ctx = LambdaContext(function_name="my_func")
    s = str(ctx)
    assert "my_func" in s
    assert "LambdaContext" in s
