# Sample Findings Walkthrough

Use this guide when practicing with the bundled sample workbooks.

## Small Complete Sample

`samples/rvtools-small-complete.xlsx` is the clean first-run workbook. It is intended to confirm that the app launches, parses RVTools data, renders each tab, and builds a Terraform handoff package.

In the app sidebar, click `Load Sample Workbook` to use this workbook directly.

## Larger Workshop Sample

`samples/SizingWorkshop-RVTools.xlsx` is intentionally less clean. Use it to practice interpreting readiness findings, package preflight output, fix categories, and VM exclusion decisions.

Expected practice findings include:

| Area | What You Should See | How To Practice |
| --- | --- | --- |
| Image import placeholders | Many VMs have unresolved custom image IDs, producing preflight warnings. | Review Image Import Planning and the generated `image-import-variables.tfvars.example`; image IDs are filled after image import. |
| Unknown target network | Export preflight can flag `unknown-net` with an invalid or blank CIDR. | In Export > Subnet CIDRs, provide a valid target CIDR before building the package. |
| `wowas3` network review | `wowas3` has a connected source NIC without a usable network name. | Treat this as source RVTools/vSphere data to correct, or exclude the VM while practicing blocker handling. |

These findings are expected for the workshop workbook. They do not mean the parser or preflight system is broken.

## Recommended Practice Flow

1. Upload `samples/SizingWorkshop-RVTools.xlsx`.
2. Review Overview and Readiness.
3. Open Remediation Backlog and VM Review.
4. Use Export > Preflight Review to inspect fix categories.
5. Correct app-planning values such as target CIDRs where appropriate.
6. Exclude intentionally blocked VMs only when practicing package build completion.
7. Build the Terraform bundle after blockers are resolved or excluded.
