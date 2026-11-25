# Add the missing bucket owner

Use the tag-bucket skill to add the freeform tag `owner` to `oci_objectstorage_bucket.pilot` in `infra/bucket.tf.json`. Read the requested value from `factory.json`. Preserve the team's existing tags and every other resource attribute. If the owner already matches, report that the ticket is complete. If the helper rejects the input, stop and report its reason.

Return the resource address, the intended diff, and the checks you ran. The reviewer will compare the candidate against the existing private bucket in OCI Resource Manager.
