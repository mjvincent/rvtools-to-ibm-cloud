import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import DraggableVmRow from '../../components/dnd/DraggableVmRow';
import PlacementModal from '../../components/dnd/PlacementModal';
import SubnetDropZone from '../../components/dnd/SubnetDropZone';
import { sampleRows } from '../../store/AppContext';

function dataTransfer() {
  const store = new Map<string, string>();
  return {
    dropEffect: '',
    effectAllowed: '',
    getData: jest.fn((type: string) => store.get(type) || ''),
    setData: jest.fn((type: string, value: string) => store.set(type, value)),
  };
}

describe('DnD components', () => {
  it('marks VM rows draggable, emits drag start, and exposes explicit clear actions', () => {
    const onDragStart = jest.fn();
    const onUnassign = jest.fn();
    render(
      <table>
        <tbody>
          <DraggableVmRow
            row={{
              ...sampleRows[0],
              subnet: 'prod-app-us-south-1',
              securityGroup: 'sg-app-private',
              overrideStorageTier: '10iops-tier',
              storageLabel: 'db_high_iops',
              wave: 'Wave 1',
            }}
            selected
            assignmentMode="network"
            onSelect={jest.fn()}
            onDragStart={onDragStart}
            onUnassign={onUnassign}
          />
        </tbody>
      </table>,
    );

    const row = screen.getByText('app-01').closest('tr');
    expect(row?.getAttribute('draggable')).toBe('true');
    expect(screen.getByText('prod-app-us-south-1')).toBeTruthy();
    expect(screen.getByText('Wave 1')).toBeTruthy();
    fireEvent.dragStart(row!, { dataTransfer: dataTransfer() });
    expect(onDragStart).toHaveBeenCalledTimes(1);

    fireEvent.click(screen.getByText('Clear subnet'));
    fireEvent.click(screen.getByText('Clear security group'));
    fireEvent.click(screen.getByText('Clear storage override'));
    fireEvent.click(screen.getByText('Clear wave'));
    expect(onUnassign).toHaveBeenCalledWith('sample-app-01', 'network');
    expect(onUnassign).toHaveBeenCalledWith('sample-app-01', 'security');
    expect(onUnassign).toHaveBeenCalledWith('sample-app-01', 'storage');
    expect(onUnassign).toHaveBeenCalledWith('sample-app-01', 'wave');
  });

  it('calls readiness action for non-ready readiness chips', () => {
    const onReadinessAction = jest.fn();
    const row = {
      ...sampleRows[1],
      migration: 'Blocked',
      migrationReasons: 'Resolve source migration finding',
    };
    render(
      <table>
        <tbody>
          <DraggableVmRow
            row={row}
            selected={false}
            assignmentMode="network"
            onSelect={jest.fn()}
            onDragStart={jest.fn()}
            onUnassign={jest.fn()}
            onReadinessAction={onReadinessAction}
          />
        </tbody>
      </table>,
    );

    fireEvent.click(screen.getByRole('button', {
      name: 'Migration readiness for db-01: Blocked. Resolve source migration finding. Open review workflow.',
    }));

    expect(onReadinessAction).toHaveBeenCalledWith('Migration', row);
  });

  it('drops VM ids onto a bucket zone', () => {
    const onDropVmIds = jest.fn();
    const transfer = dataTransfer();
    transfer.setData('application/json', JSON.stringify({ vmIds: ['vm-1', 'vm-2'] }));

    render(
      <SubnetDropZone
        bucket={{ id: 'subnet-app', name: 'prod-app-us-south-1' }}
        assignmentMode="network"
        onAssign={jest.fn()}
        onDropVmIds={onDropVmIds}
      >
        <h3>prod-app-us-south-1</h3>
      </SubnetDropZone>,
    );

    fireEvent.drop(screen.getByTestId('tile'), { dataTransfer: transfer });
    expect(onDropVmIds).toHaveBeenCalledWith(
      ['vm-1', 'vm-2'],
      expect.objectContaining({ name: 'prod-app-us-south-1' }),
    );
  });

  it('confirms pending placement', () => {
    const onConfirm = jest.fn();
    render(
      <PlacementModal
        open
        assignmentMode="wave"
        bucketName="Wave 1"
        vmCount={2}
        onCancel={jest.fn()}
        onConfirm={onConfirm}
      />,
    );

    expect(screen.getByText('Assign 2 VMs to Wave 1?')).toBeTruthy();
    fireEvent.click(screen.getByText('Assign VMs'));
    expect(onConfirm).toHaveBeenCalledTimes(1);
  });
});
