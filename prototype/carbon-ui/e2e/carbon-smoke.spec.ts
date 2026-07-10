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

async function clickRowAction(page: Page, rowIndex: number, actionText: string) {
  await page.locator('tbody tr').nth(rowIndex).evaluate((row, text) => {
    const button = Array.from(row.querySelectorAll('button')).find((candidate) =>
      candidate.textContent?.trim() === text,
    );
    if (!button) {
      throw new Error(`Could not find row action: ${text}`);
    }
    (button as HTMLButtonElement).click();
  }, actionText);
}

async function mockHealthyProjectApi(
  page: Page,
  projectId: string,
  projectName: string,
  options: {
    networkPlan?: (route: Parameters<Parameters<Page['route']>[1]>[0]) => Promise<void>;
    preview?: (route: Parameters<Parameters<Page['route']>[1]>[0]) => Promise<void>;
    terraform?: (route: Parameters<Parameters<Page['route']>[1]>[0]) => Promise<void>;
    preflight?: (route: Parameters<Parameters<Page['route']>[1]>[0]) => Promise<void>;
  } = {},
) {
  await page.route('**/health', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'ok', persistence_enabled: true }),
    });
  });
  await page.route('**/api/projects', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ projects: [] }),
      });
      return;
    }
    if (route.request().method() === 'POST') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ project: { id: projectId, name: projectName, description: '' } }),
      });
      return;
    }
    await route.continue();
  });
  await page.route(`**/api/projects/${projectId}/state`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'saved' }),
    });
  });
  await page.route(`**/api/projects/${projectId}/network-plan`, async (route) => {
    if (options.networkPlan) {
      await options.networkPlan(route);
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ status: 'saved' }),
    });
  });
  if (options.preview) {
    await page.route(`**/api/projects/${projectId}/terraform/preview`, options.preview);
  }
  if (options.terraform) {
    await page.route(`**/api/projects/${projectId}/terraform`, options.terraform);
  }
  await page.route(`**/api/projects/${projectId}/preflight`, async (route) => {
    if (options.preflight) {
      await options.preflight(route);
      return;
    }
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        project_id: projectId,
        project_name: projectName,
        summary: { blockers: 0, warnings: 0, info: 0, total: 0 },
        findings: [],
      }),
    });
  });
}

async function mockWorkbookSummary(page: Page) {
  await page.route('**/api/workbooks/summary', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        filename: 'rvtools-small-complete.xlsx',
        estate_summary: {
          in_scope: 2,
          excluded: 0,
          monthly: 0,
          savings: 0,
          blocked: 0,
          review: 1,
        },
        overview_blockers: {},
        readiness_counts: {},
        assessment_quality: {},
        readiness_rows: [],
        assignment_rows: [
          {
            'VM Key': 'app-01',
            'VM Name': 'app-01',
            'Image Readiness': 'Ready',
            'Migration Readiness': 'Ready',
            'Memory Readiness': 'Ready',
            'Network Readiness': 'Ready',
            'IBM Profile': 'bx2-2x8',
            'Storage Tier': '5iops-tier',
            Network: 'prod-app-net',
            Subnet: 'prod-app-us-south-1',
            'Security Group': 'sg-app-private',
            'Power State': 'poweredOn',
            Owner: 'Payments',
            Application: 'Payments',
            Wave: 'Wave 1',
            'Cutover Group': 'payments-cutover',
            Priority: 'High',
          },
          {
            'VM Key': 'app-02',
            'VM Name': 'app-02',
            'Image Readiness': 'Ready',
            'Migration Readiness': 'Ready',
            'Memory Readiness': 'Ready',
            'Network Readiness': 'Review',
            'IBM Profile': 'bx2-2x8',
            'Storage Tier': '5iops-tier',
            Network: 'prod-app-net',
            'Power State': 'poweredOn',
            Owner: 'Payments',
            Application: 'Payments',
            'Cutover Group': 'payments-cutover',
            Priority: 'High',
          },
        ],
      }),
    });
  });
}

async function uploadAndSaveMockedProject(page: Page, projectName: string) {
  await page.goto('/');
  await page.getByRole('link', { name: 'Workbook Intake' }).click();
  await page.locator('input[type="file"]').first().setInputFiles(sampleWorkbook);
  await expect(page.getByText(/Loaded rvtools-small-complete.xlsx/)).toBeVisible();

  await page.getByRole('button', { name: 'Save project' }).click();
  await page.getByLabel('Project name').fill(projectName);
  await page.getByRole('button', { name: /Create project|Update project/ }).click();
  await expect(page.getByText('Project saved to Postgres.')).toBeVisible();
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

test('supports keyboard navigation and accessible review routing', async ({ page }) => {
  await page.goto('/');

  await expect(page.getByRole('banner', { name: 'RVTools to IBM Cloud' })).toBeVisible();
  await expect(page.getByRole('navigation', { name: 'Workbench navigation' })).toBeVisible();
  await expect(page.locator('main')).toBeVisible();
  await expect(page.getByRole('button', { name: 'API status' })).toBeVisible();

  await page.getByRole('button', { name: 'API status' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByLabel('API status panel')).toBeVisible();
  await page.keyboard.press('Enter');
  await expect(page.getByLabel('API status panel')).toBeHidden();

  await page.getByRole('link', { name: 'Workbook Intake' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'Workbook intake' })).toBeVisible();

  await page.locator('input[type="file"]').first().setInputFiles(sampleWorkbook);
  await expect(page.getByText(/Loaded rvtools-small-complete.xlsx/)).toBeVisible();
  await expect(page.getByRole('heading', { name: 'VM Assignment Workbench' })).toBeVisible();

  await expect(page.getByRole('table', { name: 'VM assignment rows' })).toBeVisible();
  await expect(page.getByRole('group', { name: 'Assignment bucket mode' })).toBeVisible();
  await expect(page.getByRole('region', { name: 'Drop VMs on prod-app-us-south-1 subnet' })).toBeVisible();

  const firstVmName = (await page.locator('tbody tr').first().locator('strong').innerText()).trim();
  await page.getByRole('checkbox', { name: `Select ${firstVmName}` }).focus();
  await page.keyboard.press('Space');
  await expect(page.getByRole('button', { name: 'Assign 1 selected VM to prod-app-us-south-1' })).toBeVisible();

  await page.getByRole('button', { name: 'Assign 1 selected VM to prod-app-us-south-1' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByText('1 VM(s) assigned to prod-app-us-south-1.')).toBeVisible();
  await expect(page.locator('tbody')).toContainText('prod-app-us-south-1');

  const imageReview = page.getByRole('button', {
    name: /Image readiness .*Open review workflow\./,
  }).first();
  await expect(imageReview).toBeVisible();
  await imageReview.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'Image import planning' })).toBeVisible();

  await page.getByRole('link', { name: 'VM Assignment' }).focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'VM Assignment Workbench' })).toBeVisible();

  const migrationReview = page.getByRole('button', {
    name: /Migration readiness .*Open review workflow\./,
  }).first();
  await expect(migrationReview).toBeVisible();
  await migrationReview.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('heading', { name: 'Remediation backlog' })).toBeVisible();
});

test('warns clearly when persistence is unavailable', async ({ page }) => {
  await page.route('**/health', async (route) => {
    await route.fulfill({
      status: 503,
      contentType: 'application/json',
      body: JSON.stringify({ detail: 'API unavailable during smoke test' }),
    });
  });

  await page.goto('/');

  await expect(page.getByRole('button', { name: 'API status' })).toBeVisible();
  await expect(page.getByText('Persistence unavailable')).toBeVisible();
  await expect(page.getByText(/Save, load, autosave, assignment sync, and Terraform ZIP export need/)).toBeVisible();
  await expect(page.getByLabel('Project save state')).toContainText('Autosave unavailable');
  await expect(page.getByLabel('Project save state')).toContainText('Persistence offline');

  await page.getByRole('button', { name: 'API status' }).click();
  await expect(page.getByLabel('API status panel')).toContainText('API unavailable');
});

test('routes preflight blockers to remediation review', async ({ page }) => {
  const projectName = `Carbon smoke preflight ${Date.now()}`;
  const projectId = 'carbon-smoke-preflight-project';

  await mockHealthyProjectApi(page, projectId, projectName, {
    preflight: async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          project_id: projectId,
          project_name: projectName,
          summary: { blockers: 1, warnings: 0, info: 0, total: 1 },
          findings: [
            {
              Severity: 'blocker',
              Category: 'readiness',
              'Fix Category': 'Readiness',
              Subject: 'app-01',
              Message: 'Image readiness must be resolved before export.',
              Remediation: 'Review image import and blocker tracking.',
              'Fix Location': 'Readiness tab',
              'Suggested Action': 'Assign an owner and resolve the blocker.',
              'Valid Options': '',
              'Recommended Option': '',
              'Quick Fix Type': '',
              Field: 'Image',
              'Current Value': 'Blocked',
              Constraint: 'Must be Ready or explicitly remediated',
            },
          ],
        }),
      });
    },
  });
  await uploadAndSaveMockedProject(page, projectName);

  await page.getByRole('link', { name: 'Export Readiness' }).click();
  await page.getByRole('button', { name: 'Run preflight' }).click();
  await expect(page.getByRole('heading', { name: 'Package preflight' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Remediation queue' })).toBeVisible();
  await expect(page.getByText('1 blocker(s)', { exact: true })).toBeVisible();
  await expect(page.getByText('Image readiness must be resolved before export.').first()).toBeVisible();

  await page.getByRole('button', { name: 'Open remediation' }).click();
  await expect(page.getByRole('heading', { name: 'Remediation backlog' })).toBeVisible();
  await expect(page.getByText(/Review remediation blockers for app-01/)).toBeVisible();
});

test('bulk cleans up VM override profile reason gaps', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('link', { name: 'VM Overrides' }).click();
  await expect(page.getByRole('heading', { name: 'VM Overrides' })).toBeVisible();

  await page.getByRole('button', { name: 'Select visible' }).click();
  await page.getByLabel('Bulk profile override').selectOption('mx2-16x128');
  await page.getByRole('button', { name: 'Apply profile', exact: true }).click();
  await expect(page.getByText('Reason needed').first()).toBeVisible();

  await page.getByLabel('Override filter').selectOption('missingReasons');
  await expect(page.locator('tbody')).toContainText('app-01');
  await expect(page.locator('tbody')).toContainText('db-01');
  await expect(page.locator('tbody')).toContainText('web-01');

  await page.getByLabel('Bulk profile reason').fill('Bulk rightsizing approved by migration architect');
  await page.getByRole('button', { name: 'Apply profile reason' }).click();
  await expect(page.getByText('Reason needed')).toHaveCount(0);
  await expect(page.getByText('0 missing reasons')).toBeVisible();
});

test('bulk applies and audits remediation queue suggested fixes', async ({ page }) => {
  const projectName = `Carbon smoke queue ${Date.now()}`;
  const projectId = 'carbon-smoke-queue-project';

  await mockWorkbookSummary(page);
  await mockHealthyProjectApi(page, projectId, projectName);
  await uploadAndSaveMockedProject(page, projectName);

  await page.getByRole('link', { name: 'Export Readiness' }).click();
  await expect(page.getByRole('heading', { name: 'Remediation queue' })).toBeVisible();
  await expect(page.getByText('Suggested subnet: prod-app-us-south-1')).toBeVisible();
  await expect(page.getByText('Suggested security group: sg-app-private')).toBeVisible();
  await expect(page.getByText('Suggested wave: Wave 1')).toBeVisible();
  await expect(page.getByText('High confidence').first()).toBeVisible();

  await page.getByRole('button', { name: 'Select high confidence' }).click();
  await expect(page.getByText('3 selected')).toBeVisible();
  await page.getByRole('button', { name: 'Apply selected fixes' }).click();
  await expect(page.getByText(/Applied 3 suggested assignment\(s\), including 3 high-confidence item\(s\)\./)).toBeVisible();

  await expect(page.getByRole('heading', { name: 'Suggestion audit' })).toBeVisible();
  await expect(page.getByText('(blank) to prod-app-us-south-1')).toBeVisible();
  await expect(page.getByText('(blank) to sg-app-private')).toBeVisible();
  await expect(page.getByText('(blank) to Wave 1')).toBeVisible();

  await page.getByRole('link', { name: 'VM Assignment' }).click();
  const appTwoRow = page.locator('tbody tr').filter({ hasText: 'app-02' });
  await expect(appTwoRow).toContainText('prod-app-us-south-1');
  await expect(appTwoRow).toContainText('sg-app-private');
  await expect(appTwoRow).toContainText('Wave 1');

  await page.getByRole('link', { name: 'Export Readiness' }).click();
  await page.getByRole('button', { name: 'Undo suggestion' }).first().click();
  await expect(page.getByText(/Reverted suggested .* change for app-02\./)).toBeVisible();
  await expect(page.getByText('Reverted', { exact: true })).toBeVisible();
});

test('reports Terraform preview failure and allows retry', async ({ page }) => {
  const projectName = `Carbon smoke preview ${Date.now()}`;
  const projectId = 'carbon-smoke-preview-project';
  let previewAttempts = 0;

  await mockHealthyProjectApi(page, projectId, projectName, {
    preview: async (route) => {
      previewAttempts += 1;
      if (previewAttempts === 1) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Preview renderer unavailable during smoke test.' }),
        });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          project_id: projectId,
          project_name: projectName,
          files: [
            {
              path: 'README.md',
              category: 'Operator guide',
              size_bytes: 42,
              content: '# Smoke preview',
            },
          ],
        }),
      });
    },
  });
  await uploadAndSaveMockedProject(page, projectName);

  await page.getByRole('link', { name: 'Export Readiness' }).click();
  await page.getByRole('button', { name: 'Preview Terraform' }).click();
  await expect(page.getByText('Export failed')).toBeVisible();
  await expect(page.getByText('Preview renderer unavailable during smoke test.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Preview Terraform' })).toBeEnabled();

  await page.getByRole('button', { name: 'Preview Terraform' }).click();
  await expect(page.getByRole('heading', { name: 'Package preview' })).toBeVisible();
  await expect(page.getByText('Package preview generated for 1 file(s).')).toBeVisible();
  await expect(page.getByLabel('Terraform preview README.md')).toContainText('Smoke preview');
});

test('reports Terraform ZIP download failure and resets generation state', async ({ page }) => {
  const projectName = `Carbon smoke zip ${Date.now()}`;
  const projectId = 'carbon-smoke-zip-project';

  await mockHealthyProjectApi(page, projectId, projectName, {
    terraform: async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: {
            reason: 'ZIP renderer unavailable during smoke test.',
            missing_subnets: ['app-01', 'db-01'],
            missing_security_groups: ['app-01'],
          },
        }),
      });
    },
  });
  await uploadAndSaveMockedProject(page, projectName);

  await page.getByRole('link', { name: 'Export Readiness' }).click();
  await page.getByRole('button', { name: 'Download Terraform ZIP' }).click();
  await expect(page.getByText('Export failed')).toBeVisible();
  await expect(page.getByText(/ZIP renderer unavailable during smoke test\./)).toBeVisible();
  await expect(page.getByText(/Missing Subnets: app-01; db-01/)).toBeVisible();
  await expect(page.getByText(/Missing Security Groups: app-01/)).toBeVisible();
  await expect(page.getByText('[object Object]')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Download Terraform ZIP' })).toBeEnabled();
});

test('reports save-before-export failure before preview generation', async ({ page }) => {
  const projectName = `Carbon smoke save failure ${Date.now()}`;
  const projectId = 'carbon-smoke-save-failure-project';
  let networkPlanSaves = 0;
  let previewCalls = 0;

  await mockHealthyProjectApi(page, projectId, projectName, {
    networkPlan: async (route) => {
      networkPlanSaves += 1;
      if (networkPlanSaves > 1) {
        await route.fulfill({
          status: 500,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Network plan save unavailable before export.' }),
        });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'saved' }),
      });
    },
    preview: async (route) => {
      previewCalls += 1;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ project_id: projectId, project_name: projectName, files: [] }),
      });
    },
  });
  await uploadAndSaveMockedProject(page, projectName);

  await page.getByRole('link', { name: 'Export Readiness' }).click();
  await page.getByRole('button', { name: 'Preview Terraform' }).click();
  await expect(page.getByText('Export failed')).toBeVisible();
  await expect(page.getByText('Network plan save unavailable before export.')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Preview Terraform' })).toBeEnabled();
  expect(previewCalls).toBe(0);
});

test('uploads workbook and round-trips saved project state', async ({ page }) => {
  const projectName = `Carbon smoke ${Date.now()}`;
  const vpcName = `smoke-vpc-${Date.now()}`;
  const securityGroupName = `sg-smoke-${Date.now()}`;
  const profileOverride = 'mx2-16x128';
  const profileOverrideReason = 'Memory validation approved by workload owner';

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
  const uploadedFirstVmName = (await page.locator('tbody tr').first().locator('strong').innerText()).trim();

  await page.getByRole('link', { name: 'VM Overrides' }).click();
  await expect(page.getByRole('heading', { name: 'VM Overrides' })).toBeVisible();
  const uploadedOverrideRow = page.locator('tbody tr').filter({ hasText: uploadedFirstVmName }).first();
  await page.getByLabel(`Override profile for ${uploadedFirstVmName}`).selectOption(profileOverride);
  await page.getByLabel(`Profile override reason for ${uploadedFirstVmName}`).fill(profileOverrideReason);
  await expect(uploadedOverrideRow).toContainText(profileOverride);
  await expect(uploadedOverrideRow).toContainText(profileOverrideReason);
  await expect(uploadedOverrideRow).not.toContainText('Reason needed');

  await page.getByRole('link', { name: 'VM Assignment' }).click();
  await expect(page.locator('tbody tr').filter({ hasText: uploadedFirstVmName }).first()).toContainText(`Override: ${profileOverride}`);

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

  await page.getByRole('link', { name: 'VM Overrides' }).click();
  const loadedOverrideRow = page.locator('tbody tr').filter({ hasText: uploadedFirstVmName }).first();
  await expect(loadedOverrideRow).toContainText(profileOverride);
  await expect(loadedOverrideRow).toContainText(profileOverrideReason);
  await page.getByRole('link', { name: 'VM Assignment' }).click();

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
  await clickRowAction(page, 0, 'Clear subnet');
  await clickRowAction(page, 0, 'Clear security group');
  await clickRowAction(page, 0, 'Clear wave');
  const storageRow = page.locator('tbody tr').nth(1);
  await storageRow.locator('details').evaluate((details) => details.setAttribute('open', ''));
  await clickRowAction(page, 1, 'Clear storage override');
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
  await expect(page.getByLabel('Terraform preview decision-audit.csv')).toContainText(profileOverride);
  await expect(page.getByLabel('Terraform preview decision-audit.csv')).toContainText(profileOverrideReason);
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
  expect(content).toContain(profileOverride);
  expect(content).toContain(profileOverrideReason);

  const selectedProjectId = await projectSelect.inputValue();
  await page.request.delete(`/api/projects/${selectedProjectId}`);
});
