import inventory from './package-inventory.json';

export const terraformPackageFiles: string[] = inventory.terraformPackageFiles;
export const handoffPackageFiles: string[] = inventory.handoffPackageFiles;
export const carbonPackageFiles: string[] = inventory.carbonPackageFiles;

export const packageFileCount =
  terraformPackageFiles.length + handoffPackageFiles.length + carbonPackageFiles.length;
