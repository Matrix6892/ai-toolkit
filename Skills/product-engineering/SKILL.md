---
name: product-engineering
description: Implement agent-driven product changes, system design, rewrites, or language/database replacements with explicit contracts and verified results. Use for substantive engineering; routine local fixes follow the project workflow.
---

# Product engineering for agents

Deliver the authorized product behavior with an implementation another agent can locate, change and verify. A full rewrite or database/language replacement is valid scope; the existing implementation supplies evidence, not a veto.

## Load by decision

- Requirements, system boundaries, technical choices or redesign: read [system analysis and architecture](references/architecture.md).
- State, concurrency, external effects or data recovery: read [runtime](references/runtime.md).
- Verification, multi-step execution or authorized delegation: read [verification](references/verification.md).
- Toolchains, dependencies or reproducible execution: read [environment](references/environment.md).
- Work that survives a request or process: additionally read [backend jobs](references/backend-jobs.md).
- Maintenance of this package: read [sources and validation](references/sources.md).

Load relevant sections, reuse current evidence, and expand context when a dependency or contradiction requires it. A known local fix needs direct work and a relevant check.

## Contract and execution

Inputs: authorized goal, repository instructions, observable acceptance cases, available sources/tools and actual constraints. Ask only for a missing decision that changes correctness or authorization; continue independent work.

A contract states inputs, outputs, errors and caller obligations. Record it in existing types, tests or documentation beside its owner.

1. **Establish the result.** Separate required behavior, intended changes, assumptions and known defects. Follow the system-analysis questions when the solution is unclear.
2. **Locate the evidence.** Read the owning module, actual callers and relevant checks. Confirm tool and source access before relying on them.
3. **Implement the requested scope.** Use local checks to catch mistakes early, including during a full rewrite. Settle shared contracts before dependent work. A planning request produces a plan; implementation continues through verification.
4. **Verify behavior.** Compare the actual artifact with acceptance cases from a reliable source. Check affected consumers and meaningful failure cases on the relevant stack. Correct regressions and distinguish intentional behavior changes.
5. **Leave a resumable result.** Preserve commands, artifact/revision identity, essential reasons and unresolved limits. Report what is implemented, verified and available. Release task-owned resources; after interruption inspect the same work before launching more.

## Economy and delegation

Optimize context retrieval, model/tool calls, execution and correction per accepted result. Use agent/tool access and observed execution as constraints; do not infer human-staffing, stack-familiarity or manual-rewrite limits. Keep one authoritative statement per rule; handoffs carry decisions, unresolved gaps and links to contracts and evidence instead of restating the design. Add detail where it changes an action or verification.

When delegation is authorized, provide a bounded goal, accessible raw inputs, permitted writes, shared contracts, expected outcomes and runnable checks. Check access first; return artifact identity, evidence and unknowns. Assign one writer per shared change and independently verify integration. This skill grants no delegation, installation, deployment or production permissions.

## Validation status

Format, retrieval and behavioral evidence have separate limits recorded in the source note. A readable instruction or successful example does not establish general model reliability.
