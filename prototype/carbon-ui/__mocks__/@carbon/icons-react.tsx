// Mock for @carbon/icons-react — simple SVG stubs
import React from 'react';

const icon = (name: string) => ({ size, ...rest }: any) => (
  <svg data-testid={`icon-${name}`} aria-hidden="true" width={size} height={size} {...rest} />
);

export const CloudUpload = icon('cloud-upload');
export const Close = icon('close');
export const DataTable = icon('data-table');
export const DeploymentPattern = icon('deployment-pattern');
export const Download = icon('download');
export const Information = icon('information');
export const Renew = icon('renew');
export const Save = icon('save');
export const View = icon('view');
