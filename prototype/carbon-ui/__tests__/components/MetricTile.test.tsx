import React from 'react';
import { render, screen } from '@testing-library/react';
import MetricTile from '../../components/ui/MetricTile';

describe('MetricTile', () => {
  it('renders value and label', () => {
    render(<MetricTile value={42} label="In scope" />);
    expect(screen.getByText('42')).toBeTruthy();
    expect(screen.getByText('In scope')).toBeTruthy();
  });

  it('renders unit when provided', () => {
    render(<MetricTile value={100} label="Cost" unit="$/mo" />);
    expect(screen.getByText('$/mo')).toBeTruthy();
  });

  it('renders helper text when provided', () => {
    render(<MetricTile value={5} label="Blockers" helper="Signals to resolve" />);
    expect(screen.getByText('Signals to resolve')).toBeTruthy();
  });

  it('handles zero value', () => {
    render(<MetricTile value={0} label="Missing SG" />);
    expect(screen.getByText('0')).toBeTruthy();
  });

  it('handles string value', () => {
    render(<MetricTile value="N/A" label="Savings" />);
    expect(screen.getByText('N/A')).toBeTruthy();
  });

  it('renders clickable tile when onClick provided', () => {
    const onClick = jest.fn();
    render(<MetricTile value={3} label="Click me" onClick={onClick} />);
    const tile = screen.getByTestId('tile');
    tile.click();
    expect(onClick).toHaveBeenCalled();
  });
});
