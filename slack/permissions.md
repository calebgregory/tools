# Caleb Gregory's Slack App — Permissions Justification

**App purpose.** Personal CLI tooling around the Slack API for tracking my own work. Operations are read-mostly; writes are limited to my own task lists, canvases, and (eventually) my own messages. No content is sent off-platform.

**Requested user-token scopes:**

- **`lists:read`** — Read items and schemas from Slack Lists I own or am a member of. Used to render task lists in CLI views.
- **`lists:write`** — Create and update items in Slack Lists I own — e.g. push tasks generated from my local notes into the corresponding Slack List.
- **`canvases:read`** — Read canvas content for canvases I have access to. Supports CLI-driven note workflows.
- **`canvases:write`** — Create and edit canvases I own — e.g. generate a project-status canvas from local data.
- **`files:read`** — Slack stores Lists (and Canvases) as files. Required by `files.list` (to discover the list IDs I have access to) and `files.info` (to fetch a list's column schema). No file *content* exfiltration.
- **`users:read`** — Resolve user IDs to human-readable names (`users.info`, `users.list`). Powers a local cache used to translate names into IDs when assigning tasks.
- **`users:read.email`** — Resolve corporate emails to user IDs (`users.lookupByEmail`) so I can assign tasks via email (e.g. `you@example.com`) instead of `U…` IDs. Reads only the identity link — does not list or harvest emails.

**Excluded by design:** no `chat:*`, `channels:history`, `groups:history`, `im:history`, `search:*`, or `admin:*` scopes. The app cannot read message content, search the workspace, or perform any administrative actions.
