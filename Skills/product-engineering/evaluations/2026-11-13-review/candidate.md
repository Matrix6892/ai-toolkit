---
name: architecture-review
description: Review an existing architecture proposal for behavioral defects across requirements, data ownership and component guarantees.
---

# Architecture review

For each consequential requirement, reconstruct the whole path:
user decision → information and version needed → producer and authority → mutations and consumers → observable result.
Follow the same business fact across module boundaries; similar names can carry different meanings, and separate interfaces can still share a constraint.

Try to falsify the composed guarantee: construct an execution where each component obeys its contract but the user's requirement fails. Include relevant alternate write/read paths, intermediate states and changes of version or authority. Local correctness, a technology label or a global quality target does not establish the end-to-end property.

Before reporting a defect, check the proposed execution against every applicable protection in the supplied sources. State the violated requirement, source-backed steps and consequence, then the smallest boundary or contract correction. A missing premise becomes a targeted question; a documented guarantee that excludes the execution defeats the finding. Keep only material findings.
