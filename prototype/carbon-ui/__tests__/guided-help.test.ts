import { allWorkflowHelp, helpForWorkflow } from '../utils/guided-help';
import type { Workflow } from '../types/network-planning';

describe('guided help content', () => {
  const expectedWorkflows: Workflow[] = [
    'overview',
    'intake',
    'assignment',
    'overrides',
    'remediation',
    'imageImport',
    'migrationOps',
    'network',
    'security',
    'storage',
    'waves',
    'export',
  ];

  it('covers every Carbon workflow', () => {
    const workflows = allWorkflowHelp().map((entry) => entry.workflow);
    expect(workflows.sort()).toEqual([...expectedWorkflows].sort());
  });

  it('provides step-level guidance for every workflow', () => {
    allWorkflowHelp().forEach((entry) => {
      expect(entry.title).toBeTruthy();
      expect(entry.purpose).toBeTruthy();
      expect(entry.beforeContinuing.length).toBeGreaterThan(0);
      expect(entry.completeWhen.length).toBeGreaterThan(0);
      expect(entry.commonMistakes.length).toBeGreaterThan(0);
      expect(entry.nextStep).toBeTruthy();
    });
  });

  it('states the Terraform execution boundary for export', () => {
    const exportHelp = helpForWorkflow('export');
    expect(exportHelp.commonMistakes.join(' ')).toContain('runs Terraform');
    expect(exportHelp.nextStep).toContain('Terraform operator');
  });
});
