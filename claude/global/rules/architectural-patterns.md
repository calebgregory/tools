# Architectural patterns

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

## Colocate conversion logic with the target type

When converting between domain types, define the conversion function in the module that owns the target type. The module that defines `SelectedType2` should also define `type2_to_selected()`.

## Match function signatures to semantic purpose

Two principles are in tension:
- **Minimize data dependence**: Functions should depend only on what they need, limiting blast radius from upstream changes.
- **Signatures communicate intent**: `type2_to_selected(type2: Type2_entity) -> SelectedType2` immediately conveys "this converts a Type2_entity to a SelectedType2".

Resolution: For **type conversion functions** whose purpose is transforming between domain types, accept the source type. The function's identity is defined by the types it bridges. Decomposing to primitives just rewrites the constructor and loses semantic meaning.

For **utility functions** that operate on data incidentally, minimize dependence—don't accept a composite type just because that's where the data came from.

Heuristic: Would changing the input type change what the function conceptually does? If yes, use the domain type. If no, use minimal data.
