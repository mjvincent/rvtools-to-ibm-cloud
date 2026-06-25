import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import BucketCard from '../../components/ui/BucketCard';

describe('BucketCard', () => {
  it('renders title and subtitle', () => {
    render(<BucketCard title="prod-subnet" subtitle="us-south-1" items={[]} />);
    expect(screen.getByText('prod-subnet')).toBeTruthy();
    expect(screen.getByText('us-south-1')).toBeTruthy();
  });

  it('renders items list', () => {
    render(<BucketCard title="wave-1" items={['app-01', 'db-01']} />);
    expect(screen.getByText('app-01')).toBeTruthy();
    expect(screen.getByText('db-01')).toBeTruthy();
  });

  it('shows empty message when no items', () => {
    render(<BucketCard title="empty-bucket" items={[]} />);
    expect(screen.getByText('No items assigned')).toBeTruthy();
  });

  it('calls onAdd when Add button clicked', async () => {
    const onAdd = jest.fn();
    render(<BucketCard title="subnet" items={['vm-1']} onAdd={onAdd} />);
    const addButton = screen.getByText('Add');
    await userEvent.click(addButton);
    expect(onAdd).toHaveBeenCalledTimes(1);
  });

  it('does not render Add button when onAdd not provided', () => {
    render(<BucketCard title="subnet" items={[]} />);
    expect(screen.queryByText('Add')).toBeNull();
  });
});
