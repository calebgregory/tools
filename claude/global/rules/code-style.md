# Coding best practices

## Avoid redundant information

- Do not write redundant or extraneous docstrings.  A docstring should not contain a restatement of the function signature.  If there is additional context or history that's important to know about the function, its intended use, or its limitations/constraints, include that.  But don't simply restate what the function signature already says.  Apply that energy into making sure your function signature is descriptive and semantically informative while remaining concise.

- Do not write comments that are a restatement of a function call or a log statement.

## Reduce visual clutter

- Prefer building complex data inline declaratively over imperatively extending.  Example:

```py
# good:
lines = [
    "",
    "Header:",
    *_header_content(),
    "",
    "Body:",
    *_body_content(),
]

# bad:
lines: list[str] = []

lines.append("")
lines.append("Header:")
lines.extend(_header_content())
lines.append("")
lines.append("Body:")
lines.extend(_body_content())
```

- Obviously, there are cases where you cannot avoid imperatively extending a complex data instance, for example, when you are conditionally building a data-instance in a for-loop.  Follow python idioms here, but prefer the in-line style.

- For multi-line text that's mostly prose, prefer a triple-quoted string with `textwrap.dedent` over a list of strings joined with `\n`.  Scalar interpolation is fine — use an f-string with `{var}` placeholders inline; the dedented form still reads as plain prose.  The list form is only justified when you need to splice a *multi-line dynamic chunk* (e.g. `*_header_content()`) into the surrounding text — that's the case the inline-list rule above is talking about.  Example:

```py
# good:
print(textwrap.dedent(
    f"""
    How to read this table — each row is one demographic field;
    each column counts patients whose two sources disagree on that field
    (out of {n_patients} total patients in the {sample_name} sample):

      only_in_a  patients where source A has values source B doesn't
      only_in_b  patients where source B has values source A doesn't
    """
))

# bad:
print("\n".join([
    "",
    "How to read this table — each row is one demographic field;",
    "each column counts patients whose two sources disagree on that field",
    f"(out of {n_patients} total patients in the {sample_name} sample):",
    "",
    "  only_in_a  patients where source A has values source B doesn't",
    "  only_in_b  patients where source B has values source A doesn't",
    "",
]))
```

## Make encapsulation clear

- Any function, type or constant that is not used outside of the module that defines it should be prefixed with a `_`.  This communicates to the reader that the function is not intended to be an externally-consumable API, which drastically affects how the reader will interpret the function's significance:  "is it _an externally-consumable API_, and therefore has a signature I am bound to in some way?  Or is it simply an internal implementation detail that can easily change?"

## Prefer explicit data flow

- When a nested function needs to "return" a value to its enclosing scope, prefer passing that value as a function parameter rather than mutating a captured `nonlocal` variable. This makes data flow explicit.

- When returning multiple values from a function, prefer a NamedTuple over an anonymous tuple when the caller will benefit from named access (e.g., `result.confirmed` vs `result[0]`). NamedTuples also support default values, reducing boilerplate at call sites.

- For accumulating a summary or report across a loop, use a `@dataclass` with default field values rather than a plain dict or a NamedTuple constructed at the end. The dataclass makes the schema explicit and fields are directly mutable.

## Imports

- ALWAYS `import typing as ty`. Use `ty.` prefix for typing constructs (e.g., `ty.NamedTuple`, `ty.Callable`).

- Do not add new imports for names already available through existing aliases.

## Return type annotations

All function definitions must include a return type annotation. For functions that return nothing, annotate with `-> None`.

## Prefer Literal over bare str for constrained values

When a value is limited to a known set of strings, use `ty.Literal` (or a named alias of one) instead of `str`. This makes the constraint enforced by the type system rather than documented by a comment.

```py
# good:
DifferenceKind = ty.Literal["source_only", "dest_only", "diverged", "identical"]

class SyncAction(ty.NamedTuple):
    kind: DifferenceKind

# bad:
class SyncAction(ty.NamedTuple):
    kind: str  # "source_only" | "dest_only" | "diverged" | "identical"
```
