# Turn a team fix into a template release

The platform checkout uses literal tags. Analytics declares `freeform_tags = var.common_tags`, which the original worker cannot edit. The general capability is preserving inherited tags when adding an owner. The value `data-engineering` belongs in the analytics spec.

## Reproduce the gap

Run from the reference repository. The second command is expected to return `Ticket blocked: unsupported tag expression` and leave the Terraform file intact.

```sh
python3 factory.py specs/analytics.json ../analytics-sandbox
(cd ../analytics-sandbox && python3 -B .agents/skills/tag-bucket/scripts/tag_bucket.py)
```

Ask Codex in the reference checkout: **“Use evals/cases.json to explain the shared-team-tags failure. Propose one replacement for tag_rule.py under experiments/. Preserve conflict handling and idempotence. Run the same replay on your candidate.”**

The supplied candidate handles the single supported variable expression and inserts the owner as a default. Terraform's `merge` gives the inherited map precedence. An inherited owner survives. A conflicting or already-present owner produces no qualifying tag addition, which the independent plan check detects.

## Compare the same tickets

```sh
python3 -B demo.py --candidate-rule experiments/shared_tags_rule.py
```

Inspect the baseline and candidate columns and the two generated factories. The grader checks the expected Terraform document, file scope, the diagnostic on blocked input, and whether a second successful run leaves the file identical. The report includes the suite hash, candidate hash and both template fingerprints. The supplied candidate earns `ready-for-review`. Any failing candidate case earns `hold` and the command exits nonzero.

The report measures deterministic worker behavior. To measure model performance, run the same tickets with Codex on fresh checkouts using the same model and runtime settings. Compare observed token usage from the JSONL events and record missing usage as unavailable. Keep the model traces private.

## Promote, roll out, and roll back

1. In a reference repo branch, copy the reviewed rule into `template/.agents/skills/tag-bucket/scripts/tag_rule.py`. Update the skill description and the generated README with the supported input. Attach the pre-promotion report and rerun the tests. Once the same capability exists on both sides, the replay reports `no-new-coverage`.
2. Have a platform maintainer review the rule and a factory owner review its behavior. Merge and tag the release in Git. Record the previous release tag alongside the new one.
3. From the new tag, generate an analytics checkout into a **new directory** with the same spec. Compare it with the team's current checkout. Open an owner-reviewed change carrying just the reusable files and updated fingerprint. Preserve team tickets, configuration and Git history. Repeat with the platform checkout after the analytics pilot succeeds.
4. If a rollout regresses, revert the rollout commit in the affected factory. For new factories, generate from the prior template tag while the maintainer fixes the case. Infrastructure rollback is a separate reviewed Terraform change against the same stack.

A factory owner can retire a checkout by archiving its repository and removing its worker schedule. Track cloud cleanup independently in the [pilot runbook](oci-pilot.md).
