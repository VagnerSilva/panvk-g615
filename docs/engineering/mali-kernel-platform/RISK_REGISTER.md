# Risk register

Technical impact and confidence are deliberately separate. Probability is
left unknown unless the sources support an estimate.

These risks retain their historical evidence and scope. RSK-006 records the
previous modified snapshot; it is a provenance invariant, not a claim that the
current checkout is dirty. The Moto-only follow-up is in
[TECHNICAL_CONSOLIDATION.md](TECHNICAL_CONSOLIDATION.md).

| ID | Risk | Impact | Probability | Scope | Evidence / confidence | Priority | Mitigation | State |
|---|---|---|---|---|---|---|---|---|
| RSK-001 | Panthor VM_BIND/syncobj assumptions are applied to custom Kbase. | High: incorrect sparse exposure, queue failure, or invalid memory operations. | Unknown | Any Kbase profile reusing Panthor VM logic | E-002/E-003/E-009; high confidence in code/document distinction | P1 | Keep backend-specific capability gates; trace ioctl and sync contracts per kernel interface. | Open |
| RSK-002 | A proposed shadow-tile sparse design is mistaken for implemented support. | High: Vulkan feature claims exceed the executed implementation. | Unknown | Proposed Kbase sparse across v6-v14 | E-004; high confidence the source marks it design-only | P1 | Keep feature bits/queues gated until implementation, CTS, and hardware evidence exist. | Open |
| RSK-003 | CSF ioctl layouts or page assumptions do not match a target DDK/kernel. | High: initialization failure or ABI/layout corruption. | Unknown | CSF Kbase across kernel revisions/page sizes | E-005; medium-high confidence of version sensitivity | P1 | Maintain exact versioned layout fixtures; validate selector tests and target-device creation. | Open |
| RSK-004 | Placed mapping assumes dma-heap availability where only ION or no compatible heap exists. | Medium-high: `VK_ERROR_MEMORY_MAP_FAILED` or unsupported placed maps. | Unknown | Older/vendor Android kernels | E-006; medium confidence, historical worklog | P2 | Detect allocator availability and validate documented fallback/error path on each supported platform. | Open |
| RSK-005 | Async heap termination is accepted without device stress/teardown tests. | High: potential race, resource leak, queue fault, or device hang. | Unknown | CSF Kbase; historical patch 192 | E-007; high confidence validation is absent per worklog | P1 | Run bounded repeated create/submit/teardown and fault checks before claiming support. | Open |
| RSK-006 | Modified/untracked `work/mesa` is treated as pinned upstream source. | High: incorrect provenance or non-reproducible conclusions. | Not estimated | Current developer workspace | E-001/E-008; high confidence for status observed | P1 | Keep the source tree untouched; validate in a disposable clean worktree and record exact diffs there. | Open |
| RSK-007 | Historical device/CTS results are reported as current results. | Medium-high: consumers rely on stale or mismatched evidence. | Not estimated | E-006/E-007 and future summaries | Worklog provenance explicitly historical; high confidence | P2 | Carry source/build/device identifiers and evidence date in every result; rerun before release claims. | Open |
| RSK-008 | Missing F0-F5 definitions cause omissions or false completeness claims. | Medium: phase deliverables may be absent from the consolidation. | Not estimated | This documentation deliverable | E-011; high confidence for supplied workspace inventory | P1 | Obtain authoritative phase index; preserve unmapped status until reconciled. | Open |
| RSK-009 | Android WSI/gralloc compatibility is generalized from sparse or offscreen evidence. | High: swapchain/import/present failures on real devices. | Unknown | Android Kbase/Panthor configurations | FND-008; medium-high inventory confidence | P2 | Trace import, acquire, present, ownership and synchronization per platform; require target-device tests. | Open |

