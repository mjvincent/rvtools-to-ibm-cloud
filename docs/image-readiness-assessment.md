# Image Readiness Assessment

## Purpose
The image readiness assessment helps migration teams review VMware workloads before IBM Cloud VPC custom image import, replication, or migration-tool cutover.

The assessment is advisory. It does not change generated Terraform resources and does not automate VMDK conversion, Cloud Object Storage upload, or image import.

This assessment is separate from the broader migration readiness assessment. Image readiness focuses on custom image prerequisites such as boot disk size, firmware, guest OS, and guest initialization requirements. Migration readiness focuses on operational cleanup items such as snapshots, mounted media, USB devices, VMware Tools status, and RVTools health findings.

## Status Values
### `Ready`
No metadata blockers were found. The VM still needs normal migration activities such as image conversion to `qcow2` or `vhd`, Cloud Object Storage staging, IBM Cloud custom image import, and boot validation.

### `Review`
The VM has metadata or operational items that should be validated before image planning. Common examples include:
* Missing guest OS metadata
* Unrecognized guest OS metadata
* Missing firmware metadata
* Boot disk below 10 GB, which IBM Cloud rounds up during import
* Multiple disks that require separate data disk mapping
* Powered-off VM state that should be validated before export

### `Blocked`
The VM has a detected issue that should be resolved before custom image import planning. In this release, `Blocked` is used when the inferred boot disk exceeds the IBM Cloud custom image size limit of 250 GB.

## Fields
* `Image Readiness`: `Ready`, `Review`, or `Blocked`
* `Readiness Reasons`: Explanation of the status
* `Firmware`: RVTools firmware value when available
* `Boot Disk GB`: Inferred boot disk size
* `Guest Customization`: Expected initialization requirement such as `cloud-init required` or `cloudbase-init required`

## IBM Cloud VPC Assumptions
The assessment uses the following IBM Cloud VPC custom image planning defaults:
* Images must be converted to `qcow2` or `vhd`
* Images must be staged in IBM Cloud Object Storage before import
* Custom images must not exceed 250 GB
* Imported images smaller than 10 GB are rounded up to 10 GB
* Linux images should have `cloud-init` installed and active
* Windows images should have `cloudbase-init` installed and active

## Limitations
RVTools cannot prove that in-guest initialization software is installed or active. Treat the `Guest Customization` field as a requirement to validate during migration preparation.

The assessment does not inspect VMDK files directly, verify checksums, upload to Cloud Object Storage, import IBM Cloud images, or call RackWare or other migration tooling.
