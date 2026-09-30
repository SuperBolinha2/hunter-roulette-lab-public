# Security boundaries

This is an unauthenticated localhost development prototype. Never bind it to
a public interface, expose ports 38000/38001/38002, or deploy it as a public
service without a separate security/authentication design.

Only approved source modules, tests, synthetic example inventory, safe tools
and sanitized notes are included. Do not commit actual inventory.json, .env,
credentials, raw packet traces, logs, proprietary binaries/assets or Lua dumps.
The file audit is a guardrail, not proof that every possible secret is absent.
Review staged diffs before each push; report suspected leaks privately.

Local backups/.local/runtime are ignored and never sent. Updating code does
not update a save or start/install arbitrary code automatically. Do not import
unreviewed client patch scripts; native assets require explicit compatibility,
hash, backup and rollback checks.
