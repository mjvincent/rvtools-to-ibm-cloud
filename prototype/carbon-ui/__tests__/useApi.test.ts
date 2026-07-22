import {
  buildApiRecoveryMessage,
  formatApiErrorDetail,
  previewTerraform,
  uploadWorkbook,
} from '../hooks/useApi';

describe('formatApiErrorDetail', () => {
  it('keeps string error details readable', () => {
    expect(formatApiErrorDetail('Terraform generation failed.', 'Fallback')).toBe(
      'Terraform generation failed.',
    );
  });

  it('formats structured object details without object coercion', () => {
    expect(
      formatApiErrorDetail(
        {
          reason: 'Missing required target mappings.',
          missing_subnets: ['app-01', 'db-01'],
          missing_security_groups: ['app-01'],
        },
        'Fallback',
      ),
    ).toBe(
      'Reason: Missing required target mappings.; Missing Subnets: app-01; db-01; Missing Security Groups: app-01',
    );
  });

  it('formats Pydantic validation details with field locations', () => {
    expect(
      formatApiErrorDetail(
        [
          {
            loc: ['body', 0, 'boot_disk_gb'],
            msg: 'Input should be greater than or equal to 10',
          },
        ],
        'Fallback',
      ),
    ).toBe('body.0.boot_disk_gb: Input should be greater than or equal to 10');
  });

  it('falls back when detail content is empty', () => {
    expect(formatApiErrorDetail({}, 'Fallback')).toBe('Fallback');
    expect(formatApiErrorDetail([], 'Fallback')).toBe('Fallback');
  });
});

describe('API failure recovery messages', () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    jest.restoreAllMocks();
  });

  it('adds a consistent recovery hint for transport failures', async () => {
    global.fetch = jest.fn().mockRejectedValue(new TypeError('Failed to fetch'));

    await expect(
      uploadWorkbook(
        new File(['broken'], 'broken.xlsx', {
          type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        }),
      ),
    ).rejects.toThrow(
      'Workbook upload failed. Confirm the FastAPI service is running, check Docker Compose or dev-server logs, then retry.',
    );
  });

  it('adds status and recovery guidance when the API returns non-JSON errors', async () => {
    global.fetch = jest.fn().mockResolvedValue(
      {
        ok: false,
        status: 502,
        statusText: 'Bad Gateway',
        json: jest.fn().mockRejectedValue(new SyntaxError('Unexpected token <')),
      } as unknown as Response,
    );

    await expect(previewTerraform('project-1')).rejects.toThrow(
      'Terraform preview failed. HTTP 502 Bad Gateway. Confirm the FastAPI service is running, check Docker Compose or dev-server logs, then retry.',
    );
  });

  it('keeps recovery guidance text centralized', () => {
    expect(buildApiRecoveryMessage('Could not save project state.', 'HTTP 503 Service Unavailable')).toBe(
      'Could not save project state. HTTP 503 Service Unavailable. Confirm the FastAPI service is running, check Docker Compose or dev-server logs, then retry. Current browser-side planning state is kept unless you refresh or close the page.',
    );
  });
});
