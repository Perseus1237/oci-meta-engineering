# OCI bucket ownership factory

This team checkout handles one recurring ticket. It adds an `owner` freeform tag to a private OCI Object Storage bucket. `factory.json` records the owning team, the source of its tags and the SHA-256 fingerprint of the template used to create the checkout.

## Run the ticket

Start with the generated files committed in their own Git repository. Open Codex here and ask it to run `tickets/owner-tag.md`, or use a configured Codex CLI:

```sh
mkdir -p .runs
codex exec --sandbox workspace-write --json - < tickets/owner-tag.md > .runs/ticket.jsonl
git status --short
git diff -- infra/bucket.tf.json
```

For an offline run of the same helper, use `python3 -B .agents/skills/tag-bucket/scripts/tag_bucket.py`. It returns a diagnostic for unsupported expressions and owner conflicts. The reviewed template accepts literal maps. The shared-tags experiment adds support for `var.common_tags`.

## Review the change

The plan reviewer packages the committed `infra/` directory, runs a Resource Manager plan against the existing development stack and checks it with the reference repo's `verify_plan.py`. Keep the ticket, candidate commit, stack and plan job IDs together in the review. The worker has no deployment role. Consult `docs/oci-pilot.md` in the meta-engineering reference repository for bootstrap, plan review and cleanup.
