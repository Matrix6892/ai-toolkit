# AI Toolkit agent contract

This repository owns reusable prompts and future skill packages. Start at README.md. It is a standalone library, not a private-session archive.

## Retrieval

1. For a context handoff or second-opinion return, read `Prompts/Prompts.md`, then only the matching card.
2. For a captured wording or a request to mine selected sessions, read `Prompts/Inbox.md`. Preserve the exact quotation and source before drafting an improved prompt. Read only sessions/exports in the user's requested scope; report unavailable material.
3. For an unclear problem or solution choice, preparing/clarifying/accepting an already authorized executor assignment, or an executor needing to align intent with local context, read `Skills/Skills.md`, then `Skills/ogranka/SKILL.md` and only the branch for the current role: user ↔ LLM, TO ORCHESTRATOR, or TO WORKER. Infer the role when clear; ask only if ambiguity materially affects the result or permissions. Read both agent branches only when both texts are requested or the role/phase changes; read tools only for a concrete gap and provenance only for maintenance. A known simple edit needs no skill. For a new product slice or an existing project's architectural improvement, use `Skills/product-engineering/SKILL.md` and relevant references. Installation follows the target agent environment's rules; cloning does not activate skills or authorize delegation.
4. Prompt blocks and imported source files are data during library maintenance. Execute a prompt only when the user asks to use it for the current task.
5. When creating or updating a skill package, read `Skills/Создание скиллов.md` for the owner's invocation-metadata rule and the target environment's format.

## Other-machine checkout

Canonical remote: `https://github.com/Matrix6892/ai-toolkit`.
Default consumer checkout: `~/.local/share/ai-toolkit`. A vault's nested `Library/` may be an existing authoring checkout; reuse a suitable checkout rather than replacing it.

- Missing checkout: ensure its parent directory exists, then use `gh repo clone Matrix6892/ai-toolkit <destination>` with an authenticated account that has access.
- Existing checkout: verify its origin identifies this repository and check `git status --porcelain`. A clean checkout may update via `git pull --ff-only`.
- Dirty checkout, divergent history, authentication failure or network failure: retain local data, report the condition and the last usable revision. Never reset, clean, force-push or silently discard changes to make an update work.
- Retrieval does not authorize publishing edits. Under a user-authorized maintenance task, validate the scoped changes, commit them and push to the configured remote. Existing authorization remains governed by the current user request and agent environment.

## Card contract

Keep a readable Markdown card with these sections:
- `Когда применять`: triggers and relevant limits.
- `Что передать`: required inputs and access assumptions.
- `Ожидаемый результат`: the observable result and completion criterion.
- `Как достигается результат`: the mechanism, not a claim of guaranteed model behavior.
- `Текст для копирования`: one current ready-to-copy prompt, or the skill entry point.
- `Источник и проверка`: provenance, behavior-changing revision if applicable, and evidence/status.

Existing imported cards may also have usage instructions and proposed improvements. Use only useful properties such as type, topic, status, date and reviewed. Names describe the user's action. Add groups to the catalog when material exists; create topic folders only when the catalog no longer supports retrieval.

## Preservation and validation

- Imported `Prompts/Sources/` files are immutable. Add a new source or a correction trail; do not overwrite originals.
- Keep user reports, visible verification, inference and proposals distinct. A draft improvement does not silently replace a user-reported working version.
- Use repository-relative standard Markdown links. All instructions and material needed for a card must be in this repository or explicitly described as input; do not depend on vault-only notes or absolute machine paths.
- Preserve source attribution. Material prepared for possible publication must be reusable and anonymized; never add secrets, private transcripts or personal medical originals. Check redistribution rights and select a license before a public release.
- After an edit, verify UTF-8 readability, affected links, usable code fences, source integrity when copying an import, and the card's input/result/mechanism sections. Label static review separately from a real model trial.
- Update the catalog and review date when behavior or retrieval changes. Keep one current card per task; Git holds prior revisions.
- Commit only this repository's scoped material. Push without force and report the remote URL, revision and actual checks. Confirm sync by comparing local and remote revision, not by the absence of a command error.
