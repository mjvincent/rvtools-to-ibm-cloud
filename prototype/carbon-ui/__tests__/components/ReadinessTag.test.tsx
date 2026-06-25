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
});
