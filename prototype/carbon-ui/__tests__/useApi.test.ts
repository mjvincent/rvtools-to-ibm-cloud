import { formatApiErrorDetail } from '../hooks/useApi';

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
