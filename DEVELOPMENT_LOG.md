# Development Log: Multi-Tab Contention Analysis

## Overview
Moving from single-tab mapping (vInfo) to a multi-tab correlation model using vInfo, vCPU, and vHost.

## Technical Goals
- [ ] Parse `vCPU` tab for performance metrics (Ready %, Co-Stop).
- [ ] Parse `vHost` tab for physical headroom (pCores, Total MHz).
- [ ] Implement **Starving VM** detection: If Ready % > 5%, override right-sizing for performance safety.
- [ ] Implement **Zombie VM** detection: If Usage < 5% and Usage MHz < 100, flag for decommissioning.
- [ ] Calculate **N+1 Cluster Resilience**: (Total Cluster MHz - Largest Host MHz) - Total Demand.

## Data Schema
- **vInfo**: Anchor (List of VMs, Host assignments)
- **vCPU**: Performance (Contention/MHz)
- **vHost**: Infrastructure (Capacity/Headroom)
