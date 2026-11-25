# Working on the OCI meta-engineering reference

The platform team maintains the generator, template, and independent graders. Application teams own generated checkouts and OCI stacks. For a per-team ticket, work in the generated checkout and follow its AGENTS.md.

For a proposed shared improvement, reproduce the failing frozen case, change one worker rule, and run `python3 -B demo.py --candidate-rule path/to/rule.py`. Run `python3 -B -m unittest discover -s tests -v` before proposing a release. Use a separate review for changes to expected outcomes or plan acceptance criteria. Keep owner slugs, stack identifiers and credentials in the team environment.

When adding a reusable template file, include its relative path in `factory.PAYLOAD` so it enters the generated checkout and template fingerprint. The Terraform binary and OCI provider version are pinned in `template/infra/`. Validate changes with Terraform 1.5.7 and the committed dependency lock file.
