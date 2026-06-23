# Developer Onboarding Guide

Welcome to the RVTools to IBM Cloud Migration Tool project! This guide will help you get up and running with the Carbon UI integration.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Prerequisites](#prerequisites)
3. [Getting Started](#getting-started)
4. [Project Structure](#project-structure)
5. [Development Workflow](#development-workflow)
6. [Testing](#testing)
7. [Common Tasks](#common-tasks)
8. [Troubleshooting](#troubleshooting)
9. [Resources](#resources)

---

## Project Overview

### What is This Project?

The RVTools to IBM Cloud Migration Tool helps enterprises migrate VMware workloads to IBM Cloud VPC. It consists of:

1. **Streamlit App** (`app.py` + `streamlit_app/`) - Production workbench for upload, planning, and Terraform generation
2. **Carbon UI** (`prototype/carbon-ui/`) - Next.js + React + IBM Carbon Design System prototype
3. **FastAPI Backend** (`prototype/api/`) - RESTful API for network planning state
4. **Terraform Renderer** (`terraform_renderer.py`) - Generates IBM Cloud Terraform configurations

### Current Status

- **Phase 1 (Weeks 1-3)**: Foundation & Testing ✅ **75% Complete**
- **Phase 1 (Week 4)**: Documentation & Polish 🔄 **In Progress**
- **Phase 2 (Weeks 5-8)**: Terraform Integration 📅 **Planned**

### Key Decisions

- Streamlit remains production until Carbon reaches feature parity
- Carbon is not a fork; it lives in `prototype/carbon-ui/`
- Postgres is the persistence layer for saved projects
- Network planning schema bridges Carbon UI and Terraform generation

---

## Prerequisites

### Required Software

| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.9+ | Backend, Streamlit, Terraform generation |
| Node.js | 18+ | Carbon UI (Next.js) |
| npm | 9+ | Package management for Carbon UI |
| Docker | 20+ | Optional: Postgres, containerized deployment |
| Git | 2.30+ | Version control |

### Recommended Tools

- **IDE**: VS Code with Python, TypeScript, and Prettier extensions
- **API Testing**: Postman or curl
- **Database**: pgAdmin or DBeaver for Postgres inspection

### Knowledge Requirements

- **Python**: FastAPI, Pydantic, dataclasses, pytest
- **TypeScript**: React, Next.js, type definitions
- **IBM Cloud**: VPC, subnets, security groups, Terraform
- **Testing**: Jest (TypeScript), pytest (Python)

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/user/rvtools-to-ibm-cloud.git
cd rvtools-to-ibm-cloud
```

### 2. Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8
```

### 3. Set Up Carbon UI

```bash
cd prototype/carbon-ui

# Install dependencies
npm install

# Install testing dependencies
npm install --save-dev jest @types/jest ts-jest

# Return to project root
cd ../..
```

### 4. Set Up Postgres (Optional)

```bash
# Using Docker
docker run --name rvtools-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=rvtools \
  -p 5432:5432 \
  -d postgres:15

# Or use docker-compose
docker-compose up -d
```

### 5. Verify Installation

```bash
# Test Python
python -c "import fastapi; print('FastAPI OK')"

# Test Node.js
node --version

# Test npm
npm --version

# Run Python tests
python -m pytest tests/ -v

# Run TypeScript tests
cd prototype/carbon-ui && npm test
```

---

## Project Structure

```
rvtools-to-ibm-cloud/
├── app.py                          # Streamlit production app entry point
├── streamlit_app/                  # Streamlit modules
│   ├── overview_readiness.py       # Readiness assessment
│   ├── vm_review.py                # VM review and sizing
│   ├── network_storage.py          # Network and storage planning
│   ├── wave_planning.py            # Migration wave planning
│   └── package_builder.py          # Terraform ZIP generation
├── prototype/
│   ├── api/                        # FastAPI backend
│   │   ├── app.py                  # API entry point
│   │   ├── schemas.py              # Pydantic validation schemas
│   │   └── persistence.py          # Postgres persistence layer
│   └── carbon-ui/                  # Next.js + Carbon UI
│       ├── app/                    # Next.js app directory
│       ├── types/                  # TypeScript type definitions
│       │   └── network-planning.ts # Network planning schema
│       ├── utils/                  # Utility functions
│       │   └── network-validation.ts # Validation utilities
│       └── __tests__/              # Jest tests
│           ├── network-planning.test.ts
│           └── network-validation.test.ts
├── models/                         # Python data models
│   ├── migration_vm.py             # VM data model
│   ├── network.py                  # Network data model
│   ├── network_planning.py         # Network planning state
│   └── readiness.py                # Readiness assessment model
├── rvtools/                        # RVTools parser
│   ├── parser.py                   # Excel workbook parser
│   ├── workbook.py                 # Workbook abstraction
│   └── network_context.py          # Network context extraction
├── tests/                          # Python tests
│   ├── test_network_planning.py    # Network planning unit tests
│   └── test_prototype_api_network_planning.py # API integration tests
├── terraform_renderer.py           # Terraform HCL generation
├── docs/                           # Documentation
│   ├── carbon-ui-integration-summary.md
│   ├── carbon-network-schema-spec.md
│   ├── api-documentation.md
│   └── DEVELOPER_ONBOARDING.md (this file)
└── requirements.txt                # Python dependencies
```

---

## Development Workflow

### Daily Workflow

1. **Pull Latest Changes**
   ```bash
   git pull origin main
   ```

2. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Changes**
   - Edit code
   - Write tests
   - Update documentation

4. **Run Tests**
   ```bash
   # Python tests
   python -m pytest tests/ -v

   # TypeScript tests
   cd prototype/carbon-ui && npm test
   ```

5. **Commit Changes**
   ```bash
   git add .
   git commit -m "feat: add network component validation"
   ```

6. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub
   ```

### Code Style

**Python**:
- Follow PEP 8
- Use Black for formatting: `black .`
- Use type hints
- Maximum line length: 100 characters

**TypeScript**:
- Follow Airbnb style guide
- Use Prettier for formatting: `npm run format`
- Use explicit types (avoid `any`)
- Maximum line length: 100 characters

### Commit Messages

Follow Conventional Commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test changes
- `refactor:` - Code refactoring
- `chore:` - Build/tooling changes

Examples:
```
feat: add network component validation
fix: correct CIDR overlap detection
docs: update API documentation
test: add integration tests for VM assignments
```

---

## Testing

### Running Tests

**Python Unit Tests**:
```bash
# All tests
python -m pytest tests/ -v

# Specific test file
python -m pytest tests/test_network_planning.py -v

# With coverage
python -m pytest tests/ --cov=models --cov=prototype.api
```

**TypeScript Unit Tests**:
```bash
cd prototype/carbon-ui

# All tests
npm test

# Watch mode
npm test -- --watch

# With coverage
npm test -- --coverage
```

**API Integration Tests**:
```bash
# Start API server
uvicorn prototype.api.app:app --reload --port 8000

# In another terminal, run tests
python -m pytest tests/test_prototype_api_network_planning.py -v
```

### Writing Tests

**Python Test Template**:
```python
"""Test module for feature X."""

import pytest
from models.network_planning import NetworkPlanningState

def test_feature_x():
    """Test that feature X works correctly."""
    # Arrange
    state = NetworkPlanningState(...)

    # Act
    result = state.some_method()

    # Assert
    assert result == expected_value

def test_feature_x_edge_case():
    """Test feature X with edge case."""
    # Test edge case
    pass
```

**TypeScript Test Template**:
```typescript
import { functionToTest } from '../path/to/module';

describe('Feature X', () => {
  it('should do something', () => {
    // Arrange
    const input = 'test';

    // Act
    const result = functionToTest(input);

    // Assert
    expect(result).toBe('expected');
  });
});
```

---

## Common Tasks

### Task 1: Add a New Network Component Type

1. **Update TypeScript Schema** (`prototype/carbon-ui/types/network-planning.ts`):
   ```typescript
   export type NetworkComponentType =
     | 'public_gateway'
     | 'vpn_gateway'
     | 'load_balancer'
     | 'vpe_gateway'
     | 'floating_ip'
     | 'route_table'
     | 'acl'
     | 'your_new_type';  // Add here
   ```

2. **Update Python Dataclass** (`models/network_planning.py`):
   ```python
   NETWORK_COMPONENT_TYPES = [
       "public_gateway",
       "vpn_gateway",
       # ... existing types
       "your_new_type",  # Add here
   ]
   ```

3. **Update Pydantic Schema** (`prototype/api/schemas.py`):
   ```python
   class NetworkComponentSchema(BaseModel):
       type: Literal[
           "public_gateway",
           # ... existing types
           "your_new_type",  # Add here
       ]
   ```

4. **Add Tests**:
   - TypeScript: `prototype/carbon-ui/__tests__/network-planning.test.ts`
   - Python: `tests/test_network_planning.py`

5. **Update Documentation**:
   - `docs/carbon-network-schema-spec.md`
   - `docs/api-documentation.md`

### Task 2: Add a New API Endpoint

1. **Define Pydantic Schema** (`prototype/api/schemas.py`):
   ```python
   class YourRequestSchema(BaseModel):
       field1: str
       field2: int
   ```

2. **Add Endpoint** (`prototype/api/app.py`):
   ```python
   @app.post("/api/your-endpoint")
   async def your_endpoint(data: YourRequestSchema):
       # Implementation
       return {"status": "success"}
   ```

3. **Add Tests** (`tests/test_prototype_api_network_planning.py`):
   ```python
   def test_your_endpoint_success(client):
       response = client.post("/api/your-endpoint", json={...})
       assert response.status_code == 200
   ```

4. **Update Documentation** (`docs/api-documentation.md`)

### Task 3: Add Terraform Generation for New Resource

1. **Update Terraform Renderer** (`terraform_renderer.py`):
   ```python
   def render_your_resource(resource_data):
       return f"""
   resource "ibm_is_your_resource" "your_resource" {{
     name = "{resource_data['name']}"
     # ... other attributes
   }}
   """
   ```

2. **Add Tests** (`tests/test_terraform_generation.py`):
   ```python
   def test_render_your_resource():
       result = render_your_resource({...})
       assert "ibm_is_your_resource" in result
   ```

---

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'fastapi'`
**Solution**:
```bash
pip install -r requirements.txt
```

**Issue**: TypeScript errors in tests: `Cannot find name 'describe'`
**Solution**:
```bash
cd prototype/carbon-ui
npm install --save-dev @types/jest
```

**Issue**: Postgres connection error
**Solution**:
```bash
# Check if Postgres is running
docker ps | grep postgres

# Start Postgres
docker-compose up -d
```

**Issue**: Tests fail with import errors
**Solution**:
```bash
# Ensure you're in the project root
cd /path/to/rvtools-to-ibm-cloud

# Activate virtual environment
source venv/bin/activate

# Set PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### Getting Help

1. **Check Documentation**:
   - `docs/` directory
   - `README.md`
   - This onboarding guide

2. **Search Issues**:
   - GitHub Issues
   - Closed issues for similar problems

3. **Ask the Team**:
   - Slack channel: #rvtools-migration
   - Email: team@example.com

---

## Resources

### Documentation

- **Project Docs**: `docs/` directory
- **API Docs**: `docs/api-documentation.md`
- **Schema Spec**: `docs/carbon-network-schema-spec.md`
- **Architecture**: `docs/carbon-integration-diagrams.md`

### External Resources

- **IBM Cloud VPC**: https://cloud.ibm.com/docs/vpc
- **Terraform IBM Provider**: https://registry.terraform.io/providers/IBM-Cloud/ibm/latest/docs
- **FastAPI**: https://fastapi.tiangolo.com/
- **Next.js**: https://nextjs.org/docs
- **IBM Carbon Design**: https://carbondesignsystem.com/
- **Pydantic**: https://docs.pydantic.dev/
- **Jest**: https://jestjs.io/docs/getting-started

### Code Examples

- **Network Planning**: `tests/test_network_planning.py`
- **API Integration**: `tests/test_prototype_api_network_planning.py`
- **TypeScript Tests**: `prototype/carbon-ui/__tests__/`
- **Terraform Generation**: `terraform_renderer.py`

---

## Next Steps

Now that you're set up, here are some good first tasks:

1. **Explore the Codebase**:
   - Read `docs/carbon-ui-integration-summary.md`
   - Review `models/network_planning.py`
   - Examine `prototype/carbon-ui/types/network-planning.ts`

2. **Run the Tests**:
   - Python: `python -m pytest tests/ -v`
   - TypeScript: `cd prototype/carbon-ui && npm test`

3. **Start the Development Servers**:
   - Streamlit: `streamlit run app.py`
   - FastAPI: `uvicorn prototype.api.app:app --reload`
   - Carbon UI: `cd prototype/carbon-ui && npm run dev`

4. **Pick a Task**:
   - Check GitHub Issues for "good first issue" labels
   - Review the TODO list in `docs/IMPLEMENTATION_STATUS.md`
   - Ask the team for recommendations

5. **Make Your First Contribution**:
   - Fix a typo in documentation
   - Add a test case
   - Improve error messages

---

## Welcome to the Team! 🎉

You're now ready to contribute to the RVTools to IBM Cloud Migration Tool. If you have any questions, don't hesitate to ask. Happy coding!
