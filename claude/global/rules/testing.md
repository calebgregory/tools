# Testing

## Tests must be isolated

Unit tests should not share mutable state or depend on execution order. Each test must be independently runnable and independently meaningful.

## Tests must be self-contained

You should be able to understand what a test is testing by reading the test alone, without chasing down fixtures or shared context. Builder functions (that construct a valid object and accept override kwargs for the specifics under test) support this: they encapsulate how to build a valid instance while making the test-relevant values explicit at the call site.

Make builder parameters keyword-only (after `*`) with sensible defaults. This way call sites only specify the values relevant to the test, reducing visual clutter and focusing the reader on what matters.

## Use `pytest.mark.parametrize` for simple mapping tests

When the test logic is identical across cases and only input/output differs, use `pytest.mark.parametrize` instead of writing separate test methods.

## No test classes

Do not use `class Test*` to group tests. Use modules for grouping instead.

## Group tests by module, then by function

Start with a single test file per source module (e.g., `test_foo.py` for `foo.py`). When a function under test needs more than one test, promote the test file into a directory and create a sub-module per function under test:

```
# before: single file
tests/test_foo.py

# after: directory named after the source module, with one test module per function
tests/foo/__init__.py
tests/foo/test_parse_value.py
tests/foo/test_validate_input.py
```

Pytest fixtures shared across test modules go in `conftest.py`. Plain helpers (builders, constants) shared across multiple test modules go in a `shared.py` sub-module. Only create `shared.py` when a helper is actually used by more than one module — if it's only used by one, keep it in that module.

This keeps things flat until there's a real reason to add structure, and the test tree remains a refinement of the source tree.

When converting an existing `test_foo.py` into a directory, `git mv test_foo.py foo/test_foo.py` first to preserve history. Then extract per-function test modules out of it. If the original file ends up empty, delete it.

## Don't wrap the function under test in a helper

The call to the function being tested should be visible in the test body, not hidden behind a helper. Helpers are fine for constructing test data (builders, fixture factories), but the act of calling the thing under test is part of what the reader needs to see to understand the test.

## Assert whole object equivalence

When the expected object is easily constructible, assert equality against a complete instance rather than checking fields one by one. This catches missing or unexpected fields and reads as a specification.

## Use `is None` for None checks on numeric types

`if x` treats 0 as falsy, which is wrong when 0 is a valid domain value (e.g. `Identifier(0)`). Always use `if x is None` when the variable can legitimately be zero.
