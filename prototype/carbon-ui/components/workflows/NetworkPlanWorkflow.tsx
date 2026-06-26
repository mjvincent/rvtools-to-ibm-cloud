'use client';

import React from 'react';
import { Button, InlineNotification, Layer, Tag } from '@carbon/react';
import { Download } from '@carbon/icons-react';
import { useAppState } from '../../store/AppContext';
import { generateTerraform, saveNetworkPlan } from '../../hooks/useApi';
import { buildNetworkPlanBody } from '../../utils/planning-state';

export default function NetworkPlanWorkflow() {
  const { state, dispatch } = useAppState();
  const {
    resources,
    assignmentRows,
    selectedProjectId,
    projectName,
    summary,
    terraformStatus,
    terraformError,
    generatingTerraform,
  } = state;

  const components = resources.networkComponents || [];
  const canGenerateTerraform = selectedProjectId && resources.vpcs.length > 0;

  async function handleGenerateTerraform() {
    dispatch({ type: 'SET_TERRAFORM_STATUS', payload: '' });
    dispatch({ type: 'SET_TERRAFORM_ERROR', payload: '' });
    dispatch({ type: 'SET_GENERATING_TERRAFORM', payload: true });
    try {
      if (!selectedProjectId) throw new Error('Save the project before generating Terraform.');
      if (resources.vpcs.length === 0) throw new Error('Network plan must contain at least one VPC.');

      dispatch({ type: 'SET_TERRAFORM_STATUS', payload: 'Saving network plan...' });

      await saveNetworkPlan(
        selectedProjectId,
        buildNetworkPlanBody({ resources, assignmentRows, projectName, summary }),
      );

      dispatch({ type: 'SET_TERRAFORM_STATUS', payload: 'Generating Terraform package...' });
      const blob = await generateTerraform(selectedProjectId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${projectName.replace(/\s+/g, '-')}-terraform-${new Date().toISOString().split('T')[0]}.zip`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      dispatch({ type: 'SET_TERRAFORM_STATUS', payload: 'Terraform package downloaded successfully!' });
    } catch (error) {
      dispatch({
        type: 'SET_TERRAFORM_ERROR',
        payload: error instanceof Error ? error.message : 'Terraform generation failed.',
      });
    } finally {
      dispatch({ type: 'SET_GENERATING_TERRAFORM', payload: false });
    }
  }

  return (
    <Layer className="workbench-section">
      <div className="section-header">
        <div>
          <h2>Network Plan</h2>
          <p>Build the target IBM Cloud VPC network intent and watch the topology preview update as resources are added.</p>
        </div>
        <div className="network-actions">
          <Button
            kind="secondary"
            size="sm"
            onClick={() => {
              dispatch({ type: 'SET_ACTIVE_WORKFLOW', payload: 'assignment' });
              dispatch({ type: 'SET_BUCKET_MODAL', payload: 'component' });
              dispatch({
                type: 'SET_BUCKET_DRAFT',
                payload: {
                  name: '',
                  label: '',
                  type: 'Public Gateway',
                  vpcId: resources.vpcs[0]?.id || '',
                  attachment: '',
                  notes: '',
                },
              });
            }}
          >
            Create network component
          </Button>
          <Button
            kind="primary"
            size="sm"
            renderIcon={Download}
            onClick={handleGenerateTerraform}
            disabled={!canGenerateTerraform || generatingTerraform}
          >
            {generatingTerraform ? 'Generating...' : 'Generate Terraform'}
          </Button>
        </div>
      </div>

      {terraformStatus && (
        <InlineNotification
          kind="success"
          title="Success"
          subtitle={terraformStatus}
          onCloseButtonClick={() => dispatch({ type: 'SET_TERRAFORM_STATUS', payload: '' })}
          lowContrast
        />
      )}
      {terraformError && (
        <InlineNotification
          kind="error"
          title="Error"
          subtitle={terraformError}
          onCloseButtonClick={() => dispatch({ type: 'SET_TERRAFORM_ERROR', payload: '' })}
          lowContrast
        />
      )}

      <div className="network-diagram" aria-label="Generated network diagram">
        {resources.vpcs.map((vpc) => {
          const vpcSubnets = resources.subnets.filter((subnet) => subnet.vpcId === vpc.id);
          const vpcComponents = components.filter((component) => component.vpcId === vpc.id);
          return (
            <div className="diagram-vpc" key={vpc.id}>
              <div className="diagram-vpc-header">
                <div>
                  <p className="diagram-kicker">VPC</p>
                  <h3>{vpc.name}</h3>
                </div>
                <Tag type="blue">{vpc.region}</Tag>
              </div>
              <div className="diagram-lane">
                <p className="diagram-label">Subnets</p>
                <div className="diagram-node-grid">
                  {vpcSubnets.map((subnet) => (
                    <div className="diagram-node" key={subnet.id}>
                      <strong>{subnet.name}</strong>
                      <span>{subnet.zone}</span>
                      <span>{subnet.cidr || 'CIDR needed'}</span>
                      <Tag type={subnet.cidr ? 'green' : 'red'}>{subnet.purpose || 'Unlabeled'}</Tag>
                    </div>
                  ))}
                  {vpcSubnets.length === 0 && (
                    <div className="diagram-node diagram-node--empty">No subnets created yet</div>
                  )}
                </div>
              </div>
              <div className="diagram-lane">
                <p className="diagram-label">Gateways, routing, and edge services</p>
                <div className="diagram-component-grid">
                  {vpcComponents.map((component) => (
                    <div className="diagram-component" key={component.id}>
                      <Tag type="purple">{component.type}</Tag>
                      <strong>{component.name}</strong>
                      <span>{component.attachment || 'No attachment selected'}</span>
                    </div>
                  ))}
                  {vpcComponents.length === 0 && (
                    <div className="diagram-component diagram-node--empty">No network components created yet</div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="network-component-catalog">
        {[
          'Address Prefix', 'Public Gateway', 'VPN Gateway', 'VPE Gateway',
          'Transit Gateway', 'Application Load Balancer', 'Network Load Balancer',
          'Route Table', 'Security Group', 'Network ACL', 'Floating IP',
          'BYOIP Range', 'Direct Link', 'Direct Link on Classic',
        ].map((component) => (
          <Tag key={component} type="gray">{component}</Tag>
        ))}
      </div>
    </Layer>
  );
}

// Made with Bob
