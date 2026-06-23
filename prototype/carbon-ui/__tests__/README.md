# Carbon UI Tests

This directory contains unit tests for the Carbon UI network planning functionality.

## Setup

### Install Dependencies

```bash
cd prototype/carbon-ui
npm install --save-dev jest @types/jest ts-jest
```

### Configure TypeScript

The tests are already configured via `jest.config.js`. Ensure your `tsconfig.json` includes:

```json
{
  "compilerOptions": {
    "types": ["jest", "node"]
  }
}
```

## Running Tests

### Run All Tests

```bash
npm test
```

### Run Specific Test File

```bash
npm test network-planning.test.ts
npm test network-validation.test.ts
```

### Run with Coverage

```bash
npm test -- --coverage
```

### Watch Mode

```bash
npm test -- --watch
```

## Test Structure

### `network-planning.test.ts` (219 lines)

Tests for network planning type definitions and helper functions:

- **createEmptyNetworkPlan()**: Tests empty plan creation with default values
- **createInitialNetworkPlan()**: Tests initial plan with VPC, subnet, security group
- **Schema Version**: Tests version constant usage
- **UUID Generation**: Tests unique ID generation
- **Timestamp Creation**: Tests ISO format timestamps
- **Entity Relationships**: Tests VPC-subnet-security group linking

**Coverage**: 18 test cases

### `network-validation.test.ts` (438 lines)

Tests for network validation utilities:

- **isValidCidr()**: Tests CIDR notation validation (valid/invalid formats, edge cases)
- **validateSecurityRule()**: Tests security rule validation (TCP/UDP/ICMP/all protocols, port ranges, CIDR validation)
- **validateVmAssignment()**: Tests VM assignment validation (primary/secondary NICs, exclusions, required fields)
- **validateNetworkPlan()**: Tests complete plan validation (VPCs, subnets, security groups, orphaned resources)
- **detectCidrOverlaps()**: Tests CIDR overlap detection (duplicates, overlapping ranges)
- **Integration Tests**: Tests complete migration plans with multiple resources

**Coverage**: 30+ test cases

## Test Data

Tests use the helper functions from `types/network-planning.ts`:

```typescript
import { createEmptyNetworkPlan, createInitialNetworkPlan } from '../types/network-planning';

const plan = createInitialNetworkPlan('Test Project');
// Returns a plan with:
// - 1 VPC with manual address prefix mode
// - 1 address prefix (10.240.0.0/16)
// - 1 subnet (10.240.10.0/24)
// - 1 security group with default outbound rule
```

## Expected Test Results

When all dependencies are installed and tests run successfully:

```
PASS  __tests__/network-planning.test.ts
  Network Planning Helper Functions
    createEmptyNetworkPlan
      ✓ should create an empty network plan with default values
      ✓ should include metadata with default values
      ✓ should create timestamps in ISO format
      ✓ should create unique timestamps
    createInitialNetworkPlan
      ✓ should create an initial network plan with metadata
      ✓ should create a default VPC
      ✓ should create a default address prefix
      ✓ should create a default subnet
      ✓ should create a default security group
      ✓ should create a default outbound rule
      ✓ should initialize empty arrays for optional buckets
      ✓ should create consistent timestamps across all entities
      ✓ should generate unique IDs for all entities
      ✓ should create valid UUID format for IDs
      ✓ should link subnet to VPC via vpcId
      ✓ should handle different project names
      ✓ should create immutable structure (no shared references)
    Schema Version
      ✓ should export schema version constant
      ✓ should use schema version in created plans

PASS  __tests__/network-validation.test.ts
  Network Validation Utilities
    isValidCidr
      ✓ should validate correct CIDR notations (7 cases)
      ✓ should reject invalid CIDR notations (10 cases)
      ✓ should handle edge cases (4 cases)
    validateSecurityRule
      ✓ should validate a correct TCP rule
      ✓ should validate a correct UDP rule
      ✓ should validate an ICMP rule without ports
      ✓ should validate an "all" protocol rule
      ✓ should detect invalid port ranges
      ✓ should detect ports out of valid range
      ✓ should detect invalid CIDR in source
      ✓ should detect invalid CIDR in destination
      ✓ should require source or destination
    validateVmAssignment
      ✓ should validate a correct VM assignment
      ✓ should validate VM assignment with secondary NICs
      ✓ should validate excluded VM with reason
      ✓ should detect missing required fields
      ✓ should detect duplicate secondary NIC orders
    validateNetworkPlan
      ✓ should validate a correct network plan
      ✓ should validate an empty network plan
      ✓ should detect invalid VPC CIDR
      ✓ should detect invalid subnet CIDR
      ✓ should detect invalid security rules
      ✓ should detect orphaned subnets
      ✓ should detect orphaned security groups
    detectCidrOverlaps
      ✓ should detect no overlaps in non-overlapping CIDRs
      ✓ should detect exact duplicate CIDRs
      ✓ should detect overlapping CIDRs
      ✓ should handle empty CIDR list
      ✓ should handle single CIDR
      ✓ should detect multiple overlaps
    Integration Tests
      ✓ should validate a complete migration plan
      ✓ should catch multiple validation errors

Test Suites: 2 passed, 2 total
Tests:       48 passed, 48 total
Snapshots:   0 total
Time:        2.5s
```

## Coverage Goals

Target coverage thresholds (configured in `jest.config.js`):

- **Branches**: 70%
- **Functions**: 70%
- **Lines**: 70%
- **Statements**: 70%

## Troubleshooting

### Type Errors in IDE

If you see TypeScript errors like "Cannot find name 'describe'" or "Cannot find name 'expect'":

1. Install Jest types: `npm install --save-dev @types/jest`
2. Add to `tsconfig.json`:
   ```json
   {
     "compilerOptions": {
       "types": ["jest"]
     }
   }
   ```
3. Restart your TypeScript server in VS Code

### Tests Not Running

If tests don't run:

1. Verify Jest is installed: `npm list jest`
2. Check `jest.config.js` exists in `prototype/carbon-ui/`
3. Verify test files are in `__tests__/` directory
4. Check file extensions are `.test.ts` or `.test.tsx`

### Import Errors

If you see "Cannot find module" errors:

1. Verify the module paths are correct relative to `__tests__/`
2. Check that the source files exist in `types/` and `utils/`
3. Ensure `tsconfig.json` has correct `baseUrl` and `paths`

## Adding New Tests

### Test File Template

```typescript
/**
 * Unit tests for [feature name]
 */

import { functionToTest } from '../path/to/module';

describe('Feature Name', () => {
  describe('functionToTest', () => {
    it('should do something', () => {
      const result = functionToTest('input');
      expect(result).toBe('expected');
    });

    it('should handle edge cases', () => {
      expect(functionToTest('')).toBe('default');
      expect(functionToTest(null)).toThrow();
    });
  });
});
```

### Best Practices

1. **One describe block per function/class**
2. **Multiple it blocks for different scenarios**
3. **Use descriptive test names** that explain what is being tested
4. **Test happy path first**, then edge cases and errors
5. **Keep tests independent** - no shared state between tests
6. **Use helper functions** from `types/network-planning.ts` for test data
7. **Test both success and failure cases**

## Integration with CI/CD

Add to your CI pipeline:

```yaml
# .github/workflows/test.yml
- name: Run Carbon UI Tests
  run: |
    cd prototype/carbon-ui
    npm install
    npm test -- --coverage --ci
```

## Next Steps

- [ ] Install Jest dependencies
- [ ] Run tests to verify setup
- [ ] Add tests for React components
- [ ] Add E2E tests with Playwright
- [ ] Integrate with CI/CD pipeline
