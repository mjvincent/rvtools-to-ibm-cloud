# Memory Readiness and Sizing

## Purpose
Memory readiness helps teams review RAM pressure and sizing constraints before selecting an IBM Cloud VPC target profile.

The assessment uses RVTools `vMemory` telemetry when available. It is advisory, but the sizing memory value can influence the recommended IBM Cloud VSI profile because profile selection depends on CPU and RAM.

## Status Values
### `Ready`
No memory pressure or memory sizing constraints were detected.

### `Review`
The VM should be reviewed before accepting the sizing recommendation. Common examples include memory reservations, hot-add enabled, light swapping or ballooning, or a conservative active-memory reduction.

### `Blocked`
The VM has a memory condition that should be remediated before resizing. Common examples include severe swapping, severe ballooning, or a memory limit below configured memory.

## Fields
* `Memory Readiness`: `Ready`, `Review`, or `Blocked`.
* `Memory Readiness Reasons`: Explanation of the memory status.
* `Configured Memory MiB`: Source configured memory.
* `Active Memory MiB`: Active memory from RVTools.
* `Consumed Memory MiB`: Consumed memory from RVTools.
* `Ballooned Memory MiB`: Ballooned memory from RVTools.
* `Swapped Memory MiB`: Swapped memory from RVTools.
* `Memory Reservation MiB`: Configured reservation.
* `Memory Limit MiB`: Configured memory limit.
* `Memory Hot Add`: Whether memory hot-add is enabled.
* `Sizing Memory MiB`: Memory value used for profile selection.
* `Memory Sizing Basis`: Explanation of the sizing method.

## Sizing Behavior
The sizing model is intentionally conservative:
* Preserve configured memory when swapping or ballooning is detected.
* Preserve configured memory when a memory reservation exists.
* Preserve configured memory when a positive memory limit is below configured memory.
* Use active memory only when there is no pressure and active memory is materially lower than configured memory.
* Apply a 50 percent configured-memory floor when reducing based on active memory.
* Never size below 2 GiB.

## Handoff Output
The Terraform ZIP includes `memory-readiness.csv`. Use it to review memory pressure, constraints, target sizing memory, sizing basis, recommended profile, override profile, and effective profile.

The same memory readiness object is also included in `migration-manifest.json`, and summary fields are included in `vm-mapping.csv`.

## Limitations
RVTools memory data is not a replacement for long-term performance monitoring. Active memory can be low for bursty workloads at the time of collection. Treat every recommended reduction as a planning signal that still requires owner validation.

Memory readiness does not modify storage, networking, image readiness, or migration readiness rules. It only influences the recommended compute profile and provides handoff fields for review.
