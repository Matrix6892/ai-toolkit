---
name: product-engineering
description: Build a new product slice, plan or implement an existing project's architectural improvement, or prepare bounded engineering tasks for another executor. Use for substantive product and architecture work; routine local fixes use the existing project workflow.
---

# Product engineering

Turn a product goal into a small useful change with explicit behavior and evidence. This package supports the project's existing architecture; it does not prescribe a framework, directory layout, number of layers or model.

## When and what to load

- New product or architectural change: read [architecture](references/architecture.md), starting from the intended user scenario.
- Stateful jobs, concurrency, APIs, external effects or recovery: read the relevant sections of [runtime](references/runtime.md).
- Multi-step implementation, meaningful verification or authorized delegation: read [verification](references/verification.md).
- Stack, dependencies, commands or reproducibility: read [environment](references/environment.md).
- Durable agent-backed backend job: additionally read [backend jobs](references/backend-jobs.md); apply only relevant guarantees.
- Source provenance, exclusions or review status: read [sources](references/sources.md).

References are conditional, not a required reading list. Reuse current evidence. For a small local correction, keep the current project structure and perform a direct relevant check.

## Inputs and expected result

Inputs: user goal and authorized scope, repository and its instructions if it exists, one important user scenario, known constraints, and available code/tests. Name an assumption only when it affects the result. Ask for a missing decision that changes correctness while progressing independent work.

Result: an implemented and appropriately checked useful slice, or a grounded specification and transition plan when the user requested planning only. The receiving person or agent can identify the owner of state, the behavior promised to callers, relevant errors, and the next action. Existence of documents is not evidence of product usefulness.

Mechanism: connect goal → user scenario → observable behavior → owning module/contract → change → meaningful check. Use actual project commands and examples. A contract is what an operation promises, including outputs, errors and caller obligations; it can be a function signature and a test rather than a new document.

## Working sequence

1. **Orient.** For substantive work state the goal, effect, scope and proposed check briefly. Inspect project instructions, the touched module, its relevant tests and actual consumers; expand by discovered dependencies. Preserve product choices and current authorization.
2. **Choose a slice.** In a new product, implement a first useful scenario end to end before accumulating layers. In an existing project, identify a concrete difficulty or bad outcome with a code location and triggering case. Separate confirmed defects, hypotheses and optional design choices.
3. **Make behavior explicit.** For a changed boundary, record inputs/outputs, owner of writes, errors and a distinguishing example in existing project types, tests or documentation. Use a transition table only when order, retries, cancellation or recovery change correctness.
4. **Deliver within scope.** Keep implementation replaceable behind the contract and follow useful existing conventions. A plan-only request ends with checked planning artifacts; an implementation request continues to the permitted implementation and verification. Installation of tools, creation of services, deployment and delegation follow the current user's scope and environment rules.
5. **Check the next consumer.** Derive expected behavior from requirements or a reliable reference, independently of the implementation. Run checks for the affected guarantee plus one relevant consumer interaction. Reuse current checks; broaden them for new risk, changed conditions or failures. Correct regressions caused by the change.
6. **Leave usable evidence.** Keep essential reasons, executable commands and unresolved limitations in the project. Report separately what was implemented, checked, available in the intended environment and accepted. Tie a useful next step to the remaining product goal.

## Delegation when authorized

Prepare a bounded task with the goal, permitted files, consumer/provider contract, concrete examples and expected outcomes, relevant reference excerpts and runnable checks. The executor must actually have the sources and instructions; a link on the coordinator's machine is insufficient.

For an ambiguous or consequential boundary, ask the executor to explain the intended behavior and examples before dependent implementation. A routine local task needs no ceremonial understanding stage. The lead agent owns integration and independent evaluation; the executor's confidence, tests or explanation alone are not acceptance. Select models and delegation tools from the available environment; this skill neither grants delegation nor fixes a model/effort.

## Validation status

This is a portable synthesis of owner engineering guidance and source-backed backend examples. Static package validation and the independent consultation are recorded in the source note. Effect on real product work remains unmeasured until a concrete project uses it.
