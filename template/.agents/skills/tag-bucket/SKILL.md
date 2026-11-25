---
name: tag-bucket
description: Add a team's owner tag to the pilot OCI Object Storage bucket and verify the local change.
---

From the factory root, read `factory.json` and `tickets/owner-tag.md`. Run the bundled worker:

```sh
python3 -B .agents/skills/tag-bucket/scripts/tag_bucket.py
git diff --check
git diff -- infra/bucket.tf.json
```

Confirm that the only proposed change adds the requested owner while preserving existing tags. If the helper exits with a diagnostic, return it to the owner. For a successful edit, hand the diff to the plan reviewer. The cloud reviewer obtains the plan in the existing stack.
