# Publication and reading contract

## Inputs and ownership

`root` is a path to a local directory, possibly absent. `files` is a nonempty
mapping from filenames to immutable bytes. A valid name matches ASCII
`[a-z][a-z0-9_-]*\.(txt|json|csv)` in its entirety, except `manifest.json` which
is reserved. No directories or aliases are accepted. Reject an empty mapping,
a bad name, or a non-bytes value with ValueError **before creating or changing
anything under root**, and without invoking validate. Input is not mutated
concurrently. No byte-size or file-count limit is required.

Root may also contain unrelated files/directories, including under `releases/`.
They belong to other tools. Never remove or modify them. The publisher owns
CURRENT and only the new paths it creates. Even earlier successful releases are
retained: existing readers may still use them. There is no garbage collection in
this API. On failure, unpublished candidate directories/staging files MAY remain;
cleanup timing is not part of the API, but they must never become active.

Assume ordinary files/directories, no symlinks, no malicious concurrent mutation,
one publisher at a time, and a local filesystem with atomic same-directory file
replacement. Readers can overlap publication. Files may accidentally be missing
or damaged later, so reads must diagnose that. No power-loss durability/fsync,
OS crash recovery or arbitrary hostile-filesystem security is requested.

## Stable disk protocol

An absent `root/CURRENT` means no active package. Otherwise it is UTF-8 JSON
`{"release": "<id>"}`, with exactly this field; id is 32 lowercase hexadecimal
characters, naming `root/releases/<id>/`. New publish calls return distinct IDs.
The release has the named payload files and `manifest.json`, UTF-8 JSON with
exactly `{"format": 1, "files": {"name": "sha256hex", ...}}`. Files is nonempty,
its names follow the input rules, and each hash is 64 lowercase hex characters.
JSON whitespace/key order is irrelevant. Each hash covers the exact payload bytes.
These are the only two required protocol files; no private directory shape,
number of writes, temporary names or cleanup algorithm is mandated.

## Publishing and validation

A successful publish stages a **complete replacement** package, including its
manifest, then calls optional `validate(candidate_reader)` exactly once. Candidate
reads use the same names/hash/error rules as normal readers and are usable even
when there is no CURRENT. During validation, newly opened active readers must
still see the previous release (or None on first publish). The validator may read
but must not modify the root, publish recursively, or retain the candidate after
raising. It may raise any exception. Success activates this accepted package by
one atomic pointer replacement, then returns its ID.

Any failure before activation (including validator and filesystem exceptions)
propagates the original exception and leaves the previous CURRENT bytes and all
previous releases intact, or leaves CURRENT absent if none existed. It must be
possible to retry. Readers can observe the previous complete package or the new
complete package, never a partial pointer or a partially written active package.
No fallible callback or old-release cleanup belongs after activation.

## Reading and failures

`open_package` returns None only if CURRENT is absent. A malformed pointer,
invalid/missing manifest, or missing release is PackageError (retain the cause
where applicable). Validate protocol shape, not application content. A reader
captures the release ID and its manifest; its names and reads remain pinned to
that release across later publications. It may read payloads lazily.

`read(name)` raises KeyError for a name outside that captured manifest. For a
declared name, missing/unreadable bytes or a SHA-256 mismatch is PackageError.
No payload bytes may be returned on a failed integrity check. An empty payload is
valid and zero bytes/hash must be preserved. Files not declared by a manifest
are not part of that reader's package. Accidental corruption is diagnosed, not
silently replaced with data from a newer release. Underlying I/O/JSON exceptions
are chained as causes where applicable; digest mismatch needs no lower cause.
