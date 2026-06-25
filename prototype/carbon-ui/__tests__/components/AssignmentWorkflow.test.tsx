import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AssignmentWorkflow from '../../components/workflows/AssignmentWorkflow';
import { AppProvider } from '../../store/AppContext';

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
    expect(tagTexts).toContain('Review');
    expect(tagTexts).toContain('Blocked');
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
});
