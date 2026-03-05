# Architectural patterns

## Prefer reference over restatement

When documenting anything — code, configuration, processes, systems — link to the canonical source rather than restating what it says. This applies to READMEs, comments, docstrings, and any explanatory prose.

Duplication creates a sync burden: now two things must be kept in agreement. Instead, tell the reader *where* to look, not *what* they'll see. Trust that the source material is readable.

## Separate computation from side effects (functional core, imperative shell)

- Functions that compute or transform data should return results, not perform I/O (printing, file writes, network calls) directly.  Centralize side effects in a thin imperative shell that calls pure functions and acts on their return values.  A pure function's output depends only on its inputs and it produces no observable side effects — this makes it easier to test, compose, and reason about.

## Match function signatures to semantic purpose

Two principles are in tension:

- **Minimize data dependence**: Functions should depend only on what they need, limiting blast radius from upstream changes.
- **Signatures communicate intent**: `xf_vehicle_to_selected(vehicle: Vehicle) -> SelectedVehicle` immediately conveys "this converts a Vehicle object to a SelectedVehicle".

Resolution: For **type conversion functions** whose purpose is transforming between domain types, accept the source type. The function's identity is defined by the types it's transforming between. Decomposing to primitives just rewrites the constructor and loses semantic meaning.

For **utility functions** that operate on data incidentally, minimize dependence--don't accept a composite type just because that's where the data came from.

Heuristic: Would changing the input type change what the function conceptually does? If yes, use the domain type. If no, use minimal data.

## Colocate conversion logic with the target type

When converting between domain types, define the conversion function in the module that owns the target type. The module that defines `SelectedVehicle` should also define `xf_vehicle_to_selected(vehicle: Vehicle) -> SelectedVehicle`.

## Keep generic utilities domain-agnostic

Shared/utility code should not know about domain-specific data structures. Emit generic identifiers (like row IDs, primary keys) and let consumers resolve them to domain objects. This keeps utilities reusable and avoids coupling layers.

## Prefer ID-based event payloads over full object serialization

For bulk operations across boundaries (JS/Python, client/server), emit lightweight identifiers rather than serializing full objects. The receiver maintains a lookup and resolves IDs locally. Benefits:

- Faster transfer (IDs are small)
- Separation of concerns (sender doesn't know receiver's data needs)
- Flexibility (receiver can look up exactly what it needs)

## Use pre-built lookups for bulk resolution

When you'll need to resolve IDs to objects in bulk, build the lookup dict upfront at data load time rather than fetching on-demand. The data is already in memory; index it once and reuse.

## Decouple async actions from data flow

For operations that trigger state changes, consider fire-and-forget with event-based data flow rather than awaiting return values. The action triggers the work; an event delivers the result. This avoids blocking on slow serialization and keeps the action fast.

## Derive scratch directories deterministically at call time

When a function writes to a scratch/temp directory, construct the path inside the function body — not at module level. Derive a deterministic subdirectory name from the function's inputs (e.g., hashing the input sources) so that concurrent invocations with different inputs don't collide on the same filesystem.
