# Workflow — UAPI/ABI audit

## When and prerequisites

Use for handshake, version, ioctl-size/layout or mapping-cookie failures.
Complete [discovery](platform-discovery.md); identify exact userspace sources,
consumed headers, source/variant and reported device UAPI. Read
[Kbase UAPI/ABI](../references/kbase-uapi-abi.md).
Matching Moto kernel source is optional; absence must remain UNKNOWN.

## Sources and steps

1. Locate the consumed header and call site in the exact overlay/patch/applied
   snapshot. Follow [selection](../../../../scripts/apply-patches.sh:27) by
   reading, not executing it. Record which later patches modify the call.
2. Record each relevant request's type, direction, nr, encoded size, fields,
   reserved zeros, alignment/offsets and version guard. Do not borrow a JM
   definition or trust a similarly named reference header.
3. Compare the reported version against
   [110 selectors](../../../../patches/csf-v11/110-select-kbase-csf-uapi-layouts-and-16k-pages.patch:450).
   For 1.21, group 32/112/40 and heap 16/24 are predictions, not device results.
   Read cached-layout and errno handling; never force fallback on
   ENOMEM/EPERM/EACCES.
4. Trace CPU page size, USER_IO's three pages, input/output offsets, BIND cookie
   and pointer/off_t widths. Distinguish GPU granule from CPU page size.
   Check Bionic and glibc independently when an authorized build fixture exists.
5. Reuse matching logs for `CSF driver`, `uAPI version`, `page_size`,
   `queue_group_create layout`, `tiler_heap_init layout`, `mem_alloc via`.
   Record the first errno and exact stage; absence of a log proves nothing.
6. If an assertion fixture or matching kernel handler is unavailable, record
   that gap instead of constructing a supposedly authoritative ABI.
   A future fixture/build requires the disposable build workflow and approval.

## Evidence, gates and stop

Deliver a request/layout table, source locators, guard/fallback behavior,
accepted layouts if actually observed, libc-specific checks and unknown kernel
links. Static PASS is only a consistent inspected ABI; assertions do not prove
device handler compatibility. Missing mandatory runtime facts are BLOCKED;
tests not run are NOT EXECUTED.

Stop on request/layout mismatch, unexpected page/cookie, access error or
unsupported context. Do not send improvised raw ioctls to distinguish layouts,
change reserved fields to suppress an error or expand the device matrix.

## Authorization boundary

Read-only source/log review is not authorization for source application,
build/assertion execution or hardware probing. Prepare any fix as a reviewable
patch; application needs explicit approval and exact no-offset/fuzz checks.
