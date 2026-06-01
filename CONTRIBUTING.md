# Contributing

## Remote Strategy

This repository is mirrored between:

- `origin`: personal GitHub remote
- `ibm-remote`: work GitHub Enterprise remote

Keep `main` synchronized across both remotes. Before starting work, refresh refs
and confirm that both default branches agree:

```bash
git fetch --all --prune
git rev-list --left-right --count origin/main...ibm-remote/main
```

The expected result is `0 0`. If either side is ahead, reconcile `main` before
opening new work.

## Branch Workflow

1. Start from a clean, current `main`.
2. Create a scoped branch, for example `feature/<short-name>`,
   `fix/<short-name>`, or `codex/<short-name>`.
3. Keep commits focused and stage only files that belong to the change.
4. Run local validation before pushing:

```bash
venv/bin/python -m pytest
venv/bin/python scripts/validate_terraform_package.py --init-validate
```

If Terraform provider download is not available locally, at minimum run:

```bash
venv/bin/python scripts/validate_terraform_package.py
```

5. Push feature branches to both remotes when the change must be visible in
   both places:

```bash
git push -u origin HEAD
git push -u ibm-remote HEAD
```

6. Open a draft pull request first, keep CI green, then mark ready for review.
7. After merging to `main`, fetch and verify that both remotes are synchronized
   again with the `rev-list` check above.

## Generated Terraform Validation

The application exports Terraform rather than storing generated packages in the
repository. Changes to `terraform_renderer.py`, package assembly, or module
interfaces should include tests that inspect the generated package contract and
should pass the sample package validator.

## CI Workflow

A GitHub Actions workflow template is available at
`docs/github-actions-ci.yml.example`. Copy it to `.github/workflows/ci.yml`
when the GitHub Enterprise token or automation account has permission to create
or update workflow files.
