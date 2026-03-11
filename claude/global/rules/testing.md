# Testing

## Tests must be isolated

Unit tests should not share mutable state or depend on execution order. Each test must be independently runnable and independently meaningful.

## Tests must be self-contained

You should be able to understand what a test is testing by reading the test alone, without chasing down fixtures or shared context. Builder functions (that construct a valid object and accept override kwargs for the specifics under test) support this: they encapsulate how to build a valid instance while making the test-relevant values explicit at the call site.

## Use `pytest.mark.parametrize` for simple mapping tests

When the test logic is identical across cases and only input/output differs, use `pytest.mark.parametrize` instead of writing separate test methods.

## Name test classes `Test_<function_name>`

Match the snake_case of the function under test: `Test_parse_value`, not `TestParseValue`. This makes it immediately clear which function the class exercises.

## Don't wrap the function under test in a helper

The call to the function being tested should be visible in the test body, not hidden behind a helper. Helpers are fine for constructing test data (builders, fixture factories), but the act of calling the thing under test is part of what the reader needs to see to understand the test.

## Assert whole object equivalence

When the expected object is easily constructible, assert equality against a complete instance rather than checking fields one by one. This catches missing or unexpected fields and reads as a specification.

## Use `is None` for None checks on numeric types

`if x` treats 0 as falsy, which is wrong when 0 is a valid domain value (e.g. `Identifier(0)`). Always use `if x is None` when the variable can legitimately be zero.
