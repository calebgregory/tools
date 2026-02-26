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

## Make encapsulation clear

- Any function, type or constant that is not used outside of the module that defines it should be prefixed with a `_`.  This communicates to the reader that the function is not intended to be an externally-consumable API, which drastically affects how the reader will interpret the function's significance:  "is it _an externally-consumable API_, and therefore has a signature I am bound to in some way?  Or is it simply an internal implementation detail that can easily change?"

## Prefer explicit data flow

- When a nested function needs to "return" a value to its enclosing scope, prefer passing that value as a function parameter rather than mutating a captured `nonlocal` variable. This makes data flow explicit.

- When returning multiple values from a function, prefer a NamedTuple over an anonymous tuple when the caller will benefit from named access (e.g., `result.confirmed` vs `result[0]`). NamedTuples also support default values, reducing boilerplate at call sites.

## Imports

- ALWAYS `import typing as ty`. Use `ty.` prefix for typing constructs (e.g., `ty.NamedTuple`, `ty.Callable`).

- Do not add new imports for names already available through existing aliases.
