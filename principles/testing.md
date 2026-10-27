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

## Separate a test's three sections with whitespace

A unit test reads as three sections: (1) setup, (2) `result = func_under_test(inputs)`, (3) assertions. Use blank lines to segregate them.

- **Always** put a blank line between the call to the function under test (2) and the assertions (3). This is the non-negotiable one — the reader should be able to see at a glance where the act ends and verification begins.
- Put a blank line between setup (1) and the call (2) **when setup is its own statement**. If the inputs can be constructed succinctly inline in the call, setup and the call don't need separating — but the call still gets separated from the assertions.

```py
# good — three sections, each separated
def test_membership():
    small = key.Cohort(zip3="372", state="TN", year_of_birth=1985, gender="M")
    not_small = key.Cohort(zip3="376", state="TN", year_of_birth=1990, gender="F")

    parquet = _small_cohorts_parquet(dir_, [small])

    assert is_in_small_cohort(parquet, small) is True
    assert is_in_small_cohort(parquet, not_small) is False

# good — inputs constructed inline, so setup and act aren't separated; act still separated from assertions
def test_from_patient_summary():
    summary = builder(PatientSummary)(zip3="376", state="TN", gender="F", year_of_birth=1990)

    assert derive.from_patient_summary(summary) == key.Cohort(
        zip3="376", state="TN", year_of_birth=1990, gender="F"
    )
```

When a test inlines an input expression into the call _and_ into the assertion such that the three sections are illegible, prefer pulling the input into a named setup variable (e.g. `not_small`) so the sections read cleanly.

## Assert whole object equivalence

When the expected object is easily constructible, assert equality against a complete instance rather than checking fields one by one. This catches missing or unexpected fields and reads as a specification.

## Use `is None` for None checks on numeric types

`if x` treats 0 as falsy, which is wrong when 0 is a valid domain value (e.g. `Identifier(0)`). Always use `if x is None` when the variable can legitimately be zero.
