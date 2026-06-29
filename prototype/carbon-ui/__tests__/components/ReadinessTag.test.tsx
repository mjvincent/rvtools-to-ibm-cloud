import React from 'react';
import { render, screen } from '@testing-library/react';
import ReadinessTag from '../../components/ui/ReadinessTag';

describe('ReadinessTag', () => {
  it('renders Blocked status', () => {
    render(<ReadinessTag status="Blocked" />);
    const tag = screen.getByTestId('carbon-tag');
    expect(tag.textContent).toBe('Blocked');
    expect(tag.getAttribute('data-type')).toBe('red');
  });

  it('renders Review status', () => {
    render(<ReadinessTag status="Review" />);
    const tag = screen.getByTestId('carbon-tag');
    expect(tag.textContent).toBe('Review');
    expect(tag.getAttribute('data-type')).toBe('yellow');
  });

  it('renders Ready status', () => {
    render(<ReadinessTag status="Ready" />);
    const tag = screen.getByTestId('carbon-tag');
    expect(tag.textContent).toBe('Ready');
    expect(tag.getAttribute('data-type')).toBe('green');
  });

  it('renders unknown status as gray', () => {
    render(<ReadinessTag status="Unknown" />);
    const tag = screen.getByTestId('carbon-tag');
    expect(tag.getAttribute('data-type')).toBe('gray');
  });

  it('renders empty string as Unknown', () => {
    render(<ReadinessTag status="" />);
    expect(screen.getByText('Unknown')).toBeTruthy();
  });

  it('renders area prefix and accessible reason when area is provided', () => {
    render(
      <ReadinessTag
        area="Migration"
        status="Review"
        reason="Validate owner and cutover group"
        vmName="app-01"
      />,
    );
    expect(screen.getByText('MIG Review')).toBeTruthy();
    expect(screen.getByLabelText('Migration readiness for app-01: Review. Validate owner and cutover group')).toBeTruthy();
  });

  it('renders non-ready actionable readiness as a button', () => {
    const onAction = jest.fn();
    render(
      <ReadinessTag
        area="Network"
        status="Blocked"
        reason="Assign target subnet"
        vmName="db-01"
        onAction={onAction}
      />,
    );
    const action = screen.getByRole('button', {
      name: 'Network readiness for db-01: Blocked. Assign target subnet. Open review workflow.',
    });
    expect(action).toBeTruthy();
  });
});
