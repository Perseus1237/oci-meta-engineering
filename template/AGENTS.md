# OCI bucket tagging factory

Read `factory.json` for the team owner and template fingerprint. The active ticket is in `tickets/owner-tag.md`. For this ticket, use the `tag-bucket` skill. The only expected edit is to `infra/bucket.tf.json`.

Run the helper from the factory root, inspect the diff, and report the resource address, owner, and any blocker. If the existing owner differs, return the decision to the factory owner. Terraform plans and release decisions belong to the independent review stage.
