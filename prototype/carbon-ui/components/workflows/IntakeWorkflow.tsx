'use client';

import React from 'react';
import { FileUploaderDropContainer, InlineNotification, Layer, Tag } from '@carbon/react';
import { useAppState } from '../../store/AppContext';
import { sampleRows } from '../../store/AppContext';
import { uploadWorkbook } from '../../hooks/useApi';
import type { WorkbookSummary } from '../../types/network-planning';

function textValue(value: unknown) {
  return value === null || value === undefined ? '' : String(value);
}

function arrayValue(value: unknown) {
  return Array.isArray(value) ? value : [];
}

function rowsFromSummary(summary: WorkbookSummary) {
  const sourceRows = summary?.assignment_rows || summary?.readiness_rows;
  if (!sourceRows || sourceRows.length === 0) {
    return sampleRows;
  }
  return sourceRows.map((row, index) => ({
    id: textValue(row['VM Key']) || textValue(row['VM Name']) || `vm-${index + 1}`,
    name: textValue(row['VM Name']),
    image: textValue(row['Image Readiness']),
    imageReasons: textValue(row['Readiness Reasons']),
    migration: textValue(row['Migration Readiness']),
    migrationReasons: textValue(row['Migration Readiness Reasons']),
    memory: textValue(row['Memory Readiness']),
    memoryReasons: textValue(row['Memory Readiness Reasons']),
    networkReadiness: textValue(row['Network Readiness']),
    networkReasons: textValue(row['Network Readiness Reasons']),
    profile: textValue(row['IBM Profile']),
    overrideProfile: textValue(row['Override Profile']),
    overrideProfileReason: textValue(row['Override Profile Reason']),
    storageTier: textValue(row['Storage Tier']),
    overrideStorageTier: textValue(row['Override Storage Tier']),
    overrideStorageTierReason: textValue(row['Override Storage Tier Reason']),
    network: textValue(row['Network']),
    subnet: textValue(row['Subnet']),
    securityGroup: textValue(row['Security Group']),
    power: textValue(row['Power State']),
    guestOs: textValue(row['Guest OS']),
    sourceIp: textValue(row['Source IP']),
    datacenter: textValue(row['Datacenter']),
    cluster: textValue(row['Cluster']),
    host: textValue(row['Host']),
    diskCount: textValue(row['Disk Count']),
    dataDiskCount: textValue(row['Data Disk Count']),
    totalStorageGb: textValue(row['Total Storage GB']),
    firmware: textValue(row['Firmware']),
    bootDiskGb: textValue(row['Boot Disk GB']),
    configuredMemoryMib: textValue(row['Configured Memory MiB']),
    activeMemoryMib: textValue(row['Active Memory MiB']),
    consumedMemoryMib: textValue(row['Consumed Memory MiB']),
    balloonedMemoryMib: textValue(row['Ballooned Memory MiB']),
    swappedMemoryMib: textValue(row['Swapped Memory MiB']),
    memoryReservationMib: textValue(row['Memory Reservation MiB']),
    memoryLimitMib: textValue(row['Memory Limit MiB']),
    memoryHotAdd: textValue(row['Memory Hot Add']),
    sizingMemoryMib: textValue(row['Sizing Memory MiB']),
    memorySizingBasis: textValue(row['Memory Sizing Basis']),
    diskDetails: arrayValue(row['Disk Details']),
    partitionDetails: arrayValue(row['Partition Details']),
    partitionCount: textValue(row['Partition Count']),
    unmatchedPartitionCount: textValue(row['Unmatched Partition Count']),
    networkDetails: arrayValue(row['Network Details']),
    readinessFindings: arrayValue(row['Readiness Findings']),
    networkReadinessFindings: arrayValue(row['Network Readiness Findings']),
    computeMonthly: textValue(row['Compute (Mo)']),
    storageMonthly: textValue(row['Storage (Mo)']),
    monthlyCost: textValue(row['Monthly Cost']),
    baselineCostMonthly: textValue(row['Baseline Cost (Mo)']),
    savingsMonthly: textValue(row['Savings (Mo)']),
    pricingSource: textValue(row['Pricing Source']),
    pricingConfidence: textValue(row['Pricing Confidence']),
    pricingLastUpdated: textValue(row['Pricing Last Updated']),
    pricingStatus: textValue(row['Pricing Status']),
    profileHourly: textValue(row['Profile Hourly']),
    owner: textValue(row['Owner']),
    application: textValue(row['Application']),
    wave: textValue(row['Wave']),
    cutoverGroup: textValue(row['Cutover Group']),
    priority: textValue(row['Priority']),
    dependencyGroup: textValue(row['Dependency Group']),
    excluded: ['true', 'yes', '1'].includes(textValue(row['Exclude?']).toLowerCase()),
    exclusionReason: textValue(row['Exclusion Reason']),
  }));
}

export { rowsFromSummary };

export default function IntakeWorkflow() {
  const { state, dispatch } = useAppState();
  const { uploadStatus, uploadError, projectName } = state;

  async function handleUpload(_event: unknown, content: { addedFiles?: File[] }) {
    const file = content?.addedFiles?.[0];
    if (!file) return;
    dispatch({ type: 'SET_UPLOAD_STATUS', payload: `Uploading ${file.name}` });
    dispatch({ type: 'SET_UPLOAD_ERROR', payload: '' });
    try {
      const payload = await uploadWorkbook(file);
      const nextRows = rowsFromSummary(payload);
      dispatch({ type: 'SET_SUMMARY', payload });
      dispatch({ type: 'SET_ASSIGNMENT_ROWS', payload: nextRows });
      dispatch({ type: 'SET_SELECTED_VM_IDS', payload: [] });
      dispatch({ type: 'SET_PROJECT_NAME', payload: payload.filename.replace(/\.xlsx$/i, '') || projectName });
      dispatch({ type: 'SET_UPLOAD_STATUS', payload: `Loaded ${payload.filename}` });
      dispatch({ type: 'SET_ACTIVE_WORKFLOW', payload: 'assignment' });
    } catch (error) {
      dispatch({
        type: 'SET_UPLOAD_ERROR',
        payload: error instanceof Error ? error.message : 'Workbook upload failed.',
      });
      dispatch({ type: 'SET_UPLOAD_STATUS', payload: '' });
    }
  }

  return (
    <Layer className="workbench-section">
      <div className="section-header">
        <div>
          <h2>Workbook intake</h2>
          <p>Drag and drop a standard RVTools workbook to populate the live VM assignment workbench.</p>
        </div>
        <Tag type="blue">Real API integration</Tag>
      </div>
      <FileUploaderDropContainer
        accept={['.xlsx']}
        labelText="Drag and drop RVTools .xlsx here or click to upload"
        multiple={false}
        name="workbook"
        onAddFiles={handleUpload}
      />
      {uploadStatus && (
        <InlineNotification
          kind="success"
          lowContrast
          title={uploadStatus}
          subtitle="Estate summary, readiness rows, and assignment rows came from the FastAPI prototype."
        />
      )}
      {uploadError && (
        <InlineNotification
          kind="error"
          lowContrast
          title="Upload failed"
          subtitle={uploadError}
        />
      )}
    </Layer>
  );
}

// Made with Bob
