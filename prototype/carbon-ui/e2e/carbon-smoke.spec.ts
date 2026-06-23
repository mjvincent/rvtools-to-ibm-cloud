import { expect, test } from '@playwright/test';

const sampleWorkbook =
  '../../samples/rvtools-small-complete.xlsx';

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

  await page.locator('tbody input[type="checkbox"]').first().check({ force: true });
  await page.getByRole('button', { name: 'Security', exact: true }).click();
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

  const selectedProjectId = await projectSelect.inputValue();
  await page.request.delete(`/api/projects/${selectedProjectId}`);
});
