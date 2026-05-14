# Experiments

This folder contains research artifacts that are not part of the production
Streamlit app, Terraform ZIP generator, or smoke test suite.

## Pricing
`experiments/pricing/` preserves early IBM Cloud API and catalog pricing
experiments. These scripts may require IBM SDK packages, network access, and
`IBMCLOUD_API_KEY`.

Use `scripts/generate_pricing_cache.py` for the supported pricing cache
generation workflow.

## Templates
`experiments/templates/` preserves older Jinja template experiments. The current
Terraform rendering is implemented in `terraform_renderer.py`; `logic_engine.py` re-exports the supported renderer functions for compatibility.
