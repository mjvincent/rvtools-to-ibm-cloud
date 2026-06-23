import { expect, test } from '@playwright/test';

const sampleWorkbook =
  '../../samples/rvtools-small-complete.xlsx';

test('uploads workbook and round-trips saved project state', async ({ page }) => {
  const projectName = `Carbon smoke ${Date.now()}`;

  await page.goto('/');
  await expect(page.getByText('RVTools to IBM Cloud VPC')).toBeVisible();

  await page.getByRole('button', { name: 'API status' }).click();
  await expect(page.getByText(/API online/)).toBeVisible();
  await page.getByRole('button', { name: 'API status' }).click();

  await page.locator('input[type="file"]').first().setInputFiles(sampleWorkbook);
  await expect(
    page.getByText(/Loaded rvtools-small-complete.xlsx/),
  ).toBeVisible();

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

  const selectedProjectId = await projectSelect.inputValue();
  await page.request.delete(`/api/projects/${selectedProjectId}`);
});
