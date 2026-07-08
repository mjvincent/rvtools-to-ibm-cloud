import React from 'react';
import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AssignmentWorkflow from '../../components/workflows/AssignmentWorkflow';
import { AppProvider } from '../../store/AppContext';

function dataTransfer() {
  const store = new Map<string, string>();
  return {
    dropEffect: '',
    effectAllowed: '',
    getData: jest.fn((type: string) => store.get(type) || ''),
    setData: jest.fn((type: string, value: string) => store.set(type, value)),
  };
}

function renderWithProvider(ui: React.ReactElement) {
  return render(<AppProvider>{ui}</AppProvider>);
}

describe('AssignmentWorkflow', () => {
  it('renders VM assignment heading', () => {
    renderWithProvider(<AssignmentWorkflow />);
    expect(screen.getByText('VM Assignment Workbench')).toBeTruthy();
  });

  it('renders sample VM rows from default state', () => {
    renderWithProvider(<AssignmentWorkflow />);
    expect(screen.getByText('app-01')).toBeTruthy();
    expect(screen.getByText('db-01')).toBeTruthy();
    expect(screen.getByText('web-01')).toBeTruthy();
  });

  it('renders search input', () => {
    renderWithProvider(<AssignmentWorkflow />);
    expect(screen.getByRole('searchbox')).toBeTruthy();
  });

  it('renders readiness filter', () => {
    renderWithProvider(<AssignmentWorkflow />);
    expect(screen.getByText('All readiness states')).toBeTruthy();
  });

  it('renders assignment bucket mode switcher', () => {
    renderWithProvider(<AssignmentWorkflow />);
    // These labels appear in both the table header and the mode-switcher button
    expect(screen.getAllByText('Network').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Security').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Storage / IOPS').length).toBeGreaterThan(0);
    expect(screen.getAllByText('Wave').length).toBeGreaterThan(0);
  });

  it('renders VM table with readiness tags', () => {
    renderWithProvider(<AssignmentWorkflow />);
    // app-01 has migration='Review'
    const tags = screen.getAllByTestId('carbon-tag');
    const tagTexts = tags.map((t) => t.textContent);
    expect(tagTexts).toContain('MIG Review');
    expect(tagTexts).toContain('MIG Blocked');
  });

  it('shows 0 selected initially', () => {
    renderWithProvider(<AssignmentWorkflow />);
    expect(screen.getByText('0 selected')).toBeTruthy();
  });

  it('shows subnet bucket list by default', () => {
    renderWithProvider(<AssignmentWorkflow />);
    // Default resources have subnets: prod-app-us-south-1, prod-db-us-south-1
    expect(screen.getByText('prod-app-us-south-1')).toBeTruthy();
    expect(screen.getByText('prod-db-us-south-1')).toBeTruthy();
  });

  it('allows switching to Security mode', async () => {
    renderWithProvider(<AssignmentWorkflow />);
    const securityButton = screen.getByText('Security');
    await userEvent.click(securityButton);
    // After switch, security groups should be visible
    expect(screen.getByText('sg-app-private')).toBeTruthy();
  });

  it('assigns a VM by dropping it on a subnet bucket', async () => {
    renderWithProvider(<AssignmentWorkflow />);
    const transfer = dataTransfer();
    const row = screen.getByText('app-01').closest('tr');

    await userEvent.click(screen.getByText('Network'));
    fireEvent.dragStart(row!, { dataTransfer: transfer });
    fireEvent.drop(screen.getByRole('region', { name: 'Drop VMs on prod-app-us-south-1 subnet' }), {
      dataTransfer: transfer,
    });

    expect(screen.getByText('Assign 1 VM to prod-app-us-south-1?')).toBeTruthy();
    await userEvent.click(screen.getByText('Assign VMs'));
    expect(screen.getAllByText('prod-app-us-south-1').length).toBeGreaterThan(1);
  });

  it('clears a row subnet assignment without changing other assignments', async () => {
    renderWithProvider(<AssignmentWorkflow />);
    const transfer = dataTransfer();
    const row = screen.getByText('app-01').closest('tr');

    fireEvent.dragStart(row!, { dataTransfer: transfer });
    fireEvent.drop(screen.getByRole('region', { name: 'Drop VMs on prod-app-us-south-1 subnet' }), {
      dataTransfer: transfer,
    });
    await userEvent.click(screen.getByText('Assign VMs'));
    expect(screen.getAllByText('prod-app-us-south-1').length).toBeGreaterThan(1);

    const assignedRow = screen.getByText('app-01').closest('tr')!;
    await userEvent.click(within(assignedRow).getByLabelText('Placement actions for app-01'));
    await userEvent.click(within(assignedRow).getByText('Clear subnet'));

    expect(within(assignedRow).getAllByText('Unassigned').length).toBeGreaterThan(0);
  });

  it('opens Image Import Planning from non-ready image readiness chip', async () => {
    renderWithProvider(<AssignmentWorkflow />);

    await userEvent.click(screen.getByRole('button', {
      name: 'Image readiness for db-01: Review. Confirm image import path. Open review workflow.',
    }));

    expect((screen.getByRole('searchbox') as HTMLInputElement).value).toBe('db-01');
  });
});
