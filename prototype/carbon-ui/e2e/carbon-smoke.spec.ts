import { expect, test, type Page } from '@playwright/test';
import { readFile } from 'node:fs/promises';

const sampleWorkbook =
  '../../samples/rvtools-small-complete.xlsx';

type SavedProject = {
  id: string;
  name?: string;
};

async function clickRowCheckbox(page: Page, index: number) {
  await page.locator('tbody tr').nth(index).locator('input[type="checkbox"]').evaluate((input) => {
    (input as HTMLInputElement).click();
  });
}

test.afterEach(async ({ request }) => {
  const response = await request.get('/api/projects');
  if (!response.ok()) return;
  const payload = await response.json();
  const projects: SavedProject[] = Array.isArray(payload.projects) ? payload.projects : [];
  await Promise.all(
    projects
      .filter((project) => String(project.name || '').startsWith('Carbon smoke '))
      .map((project) => request.delete(`/api/projects/${project.id}`)),
  );
});

test('uploads workbook and round-trips saved project state', async ({ page }) => {
  const projectName = `Carbon smoke ${Date.now()}`;
  const vpcName = `smoke-vpc-${Date.now()}`;
  const securityGroupName = `sg-smoke-${Date.now()}`;

  await page.goto('/');
  await expect(page.getByText('RVTools to IBM Cloud VPC')).toBeVisible();
  await expect(page.getByRole('heading', { name: 'VM Assignment Workbench' })).toBeVisible();
  await expect(page.getByText('Network Plan')).toBeVisible();

  await page.getByRole('button', { name: 'API status' }).click();
  await expect(page.getByText(/API online/)).toBeVisible();
  await page.getByRole('button', { name: 'API status' }).click();

  await page.getByText('Workbook Intake').click();
  await page.locator('input[type="file"]').first().setInputFiles(sampleWorkbook);
  await expect(
    page.getByText(/Loaded rvtools-small-complete.xlsx/),
  ).toBeVisible();
  await expect(page.getByRole('heading', { name: 'VM Assignment Workbench' })).toBeVisible();

  await page.getByRole('button', { name: 'Create VPC' }).click();
  const vpcDialog = page.getByRole('dialog', { name: 'Create VPC bucket' });
  await vpcDialog.getByRole('textbox', { name: 'Name' }).fill(vpcName);
  await vpcDialog.getByRole('button', { name: 'Create bucket' }).click();
  await expect(page.getByText(`${vpcName} bucket created.`)).toBeVisible();
  await expect(page.getByLabel('Planned VPC buckets')).toContainText(vpcName);

  await page.getByText('Network Plan').click();
  await expect(page.getByLabel('Generated network diagram')).toContainText(vpcName);
  await expect(page.getByRole('button', { name: 'Create network component' })).toBeVisible();
  await page.getByRole('link', { name: 'VM Assignment' }).click();

  await page
    .locator('tbody tr')
    .first()
    .dragTo(page.locator('.bucket-tile').filter({ hasText: 'prod-app-us-south-1' }));
  await expect(page.getByRole('dialog', { name: 'Confirm VM placement' })).toBeVisible();
  await page.getByRole('button', { name: 'Assign VMs' }).click();
  await expect(page.locator('tbody')).toContainText('prod-app-us-south-1');

  await page.getByLabel('Assignment bucket mode').getByRole('button', { name: 'Security', exact: true }).click();
  await page.getByRole('button', { name: 'Create bucket' }).click();
  const bucketDialog = page.getByRole('dialog', { name: 'Create security bucket' });
  await bucketDialog.getByRole('textbox', { name: 'Name' }).fill(securityGroupName);
  await bucketDialog.getByLabel('Purpose label').fill('Smoke test security group');
  await bucketDialog.getByRole('button', { name: 'Create bucket' }).click();
  await expect(page.getByText(`${securityGroupName} bucket created.`)).toBeVisible();
  await page
    .locator('.bucket-tile')
    .filter({ hasText: securityGroupName })
    .getByRole('button', { name: 'Assign' })
    .click();
  await expect(page.getByText(new RegExp(`1 VM\\(s\\) assigned to ${securityGroupName}`))).toBeVisible();
  await expect(page.locator('tbody')).toContainText(securityGroupName);

  await page.getByRole('button', { name: 'Save project' }).click();
  await page.getByLabel('Project name').fill(projectName);
  await page
    .getByLabel('Description')
    .fill('Created by automated Carbon smoke test');
  await page
    .getByRole('button', { name: /Create project|Update project/ })
    .click();
  await expect(page.getByText('Project saved to Postgres.')).toBeVisible();
  await expect
    .poll(async () => {
      const options = await page.locator('#project option').allTextContents();
      return options.some((text) => text.includes(projectName));
    })
    .toBe(true);

  await page.reload();
  await expect(page.getByText('RVTools to IBM Cloud VPC')).toBeVisible();

  const projectSelect = page.locator('#project');
  let savedOption = '';
  await expect
    .poll(async () => {
      const optionTexts = await projectSelect.locator('option').allTextContents();
      savedOption = optionTexts.find((text) => text.includes(projectName)) || '';
      return savedOption;
    })
    .toContain(projectName);
  expect(savedOption).toBeTruthy();

  await projectSelect.selectOption({ label: savedOption });
  await page.getByRole('button', { name: 'Load', exact: true }).click();
  await expect(page.getByText(new RegExp(`Loaded ${projectName}`))).toBeVisible();
  await expect(page.locator('tbody')).toContainText(securityGroupName);

  const firstVmName = (await page.locator('tbody tr').first().locator('strong').innerText()).trim();
  await expect(page.getByRole('checkbox', { name: `Select ${firstVmName}` })).toBeVisible();

  await clickRowCheckbox(page, 0);
  await clickRowCheckbox(page, 1);

  await page.getByLabel('Assignment bucket mode').getByRole('button', { name: 'Network', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Drop VMs on prod-db-us-south-1 subnet' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Assign 2 selected VMs to prod-db-us-south-1' })).toBeVisible();
  await page
    .locator('tbody tr')
    .first()
    .dragTo(page.locator('.bucket-tile').filter({ hasText: 'prod-db-us-south-1' }));
  await expect(page.getByRole('dialog', { name: 'Confirm VM placement' })).toBeVisible();
  await expect(page.getByText('Assign 2 VMs to prod-db-us-south-1?')).toBeVisible();
  await page.getByRole('button', { name: 'Assign VMs' }).click();
  await expect(page.getByText('2 VM(s) assigned to prod-db-us-south-1.')).toBeVisible();
  await expect(page.locator('tbody')).toContainText('prod-db-us-south-1');

  await page.getByLabel('Assignment bucket mode').getByRole('button', { name: 'Security', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Drop VMs on sg-db-private security group' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Assign 2 selected VMs to sg-db-private' })).toBeVisible();
  await page
    .locator('tbody tr')
    .first()
    .dragTo(page.locator('.bucket-tile').filter({ hasText: 'sg-db-private' }));
  await expect(page.getByRole('dialog', { name: 'Confirm VM placement' })).toBeVisible();
  await expect(page.getByText('Assign 2 VMs to sg-db-private?')).toBeVisible();
  await page.getByRole('button', { name: 'Assign VMs' }).click();
  await expect(page.getByText('2 VM(s) assigned to sg-db-private.')).toBeVisible();
  await expect(page.locator('tbody')).toContainText('sg-db-private');

  await page.getByLabel('Assignment bucket mode').getByRole('button', { name: 'Storage / IOPS', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Drop VMs on Database high IOPS storage profile' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Assign 2 selected VMs to Database high IOPS' })).toBeVisible();
  await page
    .locator('tbody tr')
    .first()
    .dragTo(page.locator('.bucket-tile').filter({ hasText: 'Database high IOPS' }));
  await expect(page.getByRole('dialog', { name: 'Confirm VM placement' })).toBeVisible();
  await expect(page.getByText('Assign 2 VMs to Database high IOPS?')).toBeVisible();
  await page.getByRole('button', { name: 'Assign VMs' }).click();
  await expect(page.getByText('2 VM(s) assigned to Database high IOPS.')).toBeVisible();
  await expect(page.locator('tbody')).toContainText('10iops-tier');

  await page.getByLabel('Assignment bucket mode').getByRole('button', { name: 'Wave', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Drop VMs on Wave 1 migration wave' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Assign 2 selected VMs to Wave 1' })).toBeVisible();
  await page
    .locator('tbody tr')
    .first()
    .dragTo(page.locator('.bucket-tile').filter({ hasText: 'Wave 1' }));
  await expect(page.getByRole('dialog', { name: 'Confirm VM placement' })).toBeVisible();
  await expect(page.getByText('Assign 2 VMs to Wave 1?')).toBeVisible();
  await page.getByRole('button', { name: 'Assign VMs' }).click();
  await expect(page.getByText('2 VM(s) assigned to Wave 1.')).toBeVisible();
  await expect(page.locator('tbody')).toContainText('Wave 1');
  await expect(page.getByText('Planning changes saved.')).toBeVisible();

  const appRow = page.locator('tbody tr').first();
  await appRow.locator('details').evaluate((details) => details.setAttribute('open', ''));
  await appRow.locator('button', { hasText: 'Clear subnet' }).click({ force: true });
  await appRow.locator('button', { hasText: 'Clear security group' }).click({ force: true });
  await appRow.locator('button', { hasText: 'Clear wave' }).click({ force: true });
  const storageRow = page.locator('tbody tr').nth(1);
  await storageRow.locator('details').evaluate((details) => details.setAttribute('open', ''));
  await storageRow.locator('button', { hasText: 'Clear storage override' }).click({ force: true });
  await expect(page.getByText('Planning changes saved.')).toBeVisible();
  await expect(appRow).not.toContainText('prod-app-us-south-1');
  await expect(appRow).not.toContainText('prod-db-us-south-1');
  await expect(appRow).not.toContainText('sg-db-private');
  await expect(appRow).not.toContainText('Wave 1');
  await expect(storageRow).not.toContainText('10iops-tier');

  await page.reload();
  await expect(page.getByText('RVTools to IBM Cloud VPC')).toBeVisible();
  await expect
    .poll(async () => {
      const optionTexts = await projectSelect.locator('option').allTextContents();
      savedOption = optionTexts.find((text) => text.includes(projectName)) || '';
      return savedOption;
    })
    .toContain(projectName);
  await projectSelect.selectOption({ label: savedOption });
  await page.getByRole('button', { name: 'Load', exact: true }).click();
  await expect(page.getByText(new RegExp(`Loaded ${projectName}`))).toBeVisible();
  await expect(page.locator('tbody')).toContainText('prod-db-us-south-1');
  await expect(page.locator('tbody')).toContainText('sg-db-private');
  await expect(page.locator('tbody')).toContainText('10iops-tier');
  await expect(page.locator('tbody')).toContainText('Wave 1');
  const reloadedAppRow = page.locator('tbody tr').first();
  await expect(reloadedAppRow).not.toContainText('prod-app-us-south-1');
  await expect(reloadedAppRow).not.toContainText('prod-db-us-south-1');
  await expect(reloadedAppRow).not.toContainText('sg-db-private');
  await expect(reloadedAppRow).not.toContainText('Wave 1');
  const reloadedStorageRow = page.locator('tbody tr').nth(1);
  await expect(reloadedStorageRow).toContainText('prod-db-us-south-1');
  await expect(reloadedStorageRow).not.toContainText('10iops-tier');

  await page.getByRole('link', { name: 'Export Readiness' }).click();
  await expect(page.getByRole('heading', { name: 'Export readiness' })).toBeVisible();
  await page.getByRole('button', { name: 'Preview Terraform' }).click();
  await expect(page.getByRole('heading', { name: 'Package preview' })).toBeVisible();
  await expect(page.getByText(/37 generated file\(s\)/)).toBeVisible();
  await page.getByRole('button', { name: 'Show handoff CSVs' }).click();
  await page.getByRole('button', { name: /decision-audit.csv/ }).click();
  await expect(page.getByLabel('Terraform preview decision-audit.csv')).toContainText('VM Name');
  await page.getByRole('button', { name: /remediation-backlog.csv/ }).click();
  await expect(page.getByLabel('Terraform preview remediation-backlog.csv')).toContainText('Blocker Type');
  await page.getByRole('button', { name: /image-import-plan.csv/ }).click();
  await expect(page.getByLabel('Terraform preview image-import-plan.csv')).toContainText('Source Image');
  await page.getByRole('button', { name: /decision-audit.csv/ }).click();

  const downloadPromise = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Download selected' }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('decision-audit.csv');
  const downloadPath = await download.path();
  expect(downloadPath).toBeTruthy();
  const content = await readFile(downloadPath as string, 'utf8');
  expect(content).toContain('VM Key,VM Name,Owner,Application,Wave,Original Profile,Chosen Profile');

  const selectedProjectId = await projectSelect.inputValue();
  await page.request.delete(`/api/projects/${selectedProjectId}`);
});
