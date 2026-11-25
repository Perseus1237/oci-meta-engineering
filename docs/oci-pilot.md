# Run the first OCI pilot

Use one development compartment, one team checkout, and one Resource Manager stack. The ticket assumes the stack already manages an unowned private bucket at `oci_objectstorage_bucket.pilot`. A new stack will correctly produce a **create**, which the ownership gate rejects. Follow the bootstrap below if you need a disposable baseline.

## Run the replay in OCI DevOps

Connect this reference Git repository as the primary source of a Managed Build stage in an OCI DevOps project. Choose a build image with Git and Python 3.8+ and use the root `build_spec.yaml`. Run the build on a reviewed revision. The stage executes the tests and prints a six-case replay with the same exit status as the local demo. The generated directories live on the ephemeral runner. The build log retains the scores. [OCI build specifications](https://docs.oracle.com/en-us/iaas/Content/devops/using/build_specs.htm)

## Place the Codex worker

For the first live ticket, use a team-controlled development VM on OCI Compute with Git, Python 3.8+, an authenticated Codex CLI, and approved connectivity to its model endpoint. Clone the generated factory and run the README's Codex command in a clean ticket branch. Use a worker account with access to the ticket and checkout. Keep the OCI plan credentials with the reviewer. Inspect the resulting diff, then commit the ticket change and submit it through your team's review process.

For the OKE deployment in the diagram, package those same tools in an image pinned by digest in OCIR. Give each Kubernetes Job an ephemeral checkout of the selected commit and run the same stdin command. A trusted collector can retain the patch, task ID, commit and measured usage. Use an enhanced cluster for workload identity and bind OCI permissions to the intended cluster, namespace and service account. A separate proxy can use Vault for model credentials. Send redacted diagnostics to Logging and restricted evidence to Object Storage. The cluster, image, model proxy, and scheduled replay are deployment choices for the hosting team. [OKE workload identity](https://docs.oracle.com/en-us/iaas/Content/ContEng/Tasks/contenggrantingworkloadaccesstoresources.htm)

## Establish the baseline once

Use a reviewer workstation with Git, the OCI CLI configured for the target region, and a checked-out trusted release of the reference repo. The following steps start **in the generated factory repo** after the README's setup. Record the absolute path of your separate reference repo for the final review command.

```sh
umask 077
mkdir -p .runs
run_dir=$(mktemp -d .runs/plan.XXXXXX)
git archive --format=zip --output="$run_dir/baseline.zip" pilot-baseline:infra
```

1. In OCI Resource Manager, create a stack from `baseline.zip` in the development compartment. The Terraform files are at the ZIP root. Select Terraform **1.5.x**. The module pins OCI provider **7.25.0** and carries its dependency lock. Leave automatic apply off. [Create a ZIP-backed stack](https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Tasks/create-stack-local.htm) · [Supported Terraform versions](https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Reference/terraformversions.htm)
2. Set `region`, `compartment_ocid`, `namespace` (the tenancy's Object Storage namespace), and `bucket_name` (a unique disposable name). For the analytics example, `common_tags` supplies the inherited tags. Use a baseline with no owner. [OCI bucket resource](https://docs.oracle.com/en-us/iaas/tools/terraform-provider-oci/latest/docs/r/objectstorage_bucket.html)
3. Run a bootstrap **Plan**. Expect one private bucket creation and inspect the name, compartment and access type. An authorized operator can apply that reviewed bootstrap plan to establish the pilot state. Record its stack ID. For a previously provisioned pilot, use the same stack and confirm a baseline plan has zero changes. Keep the bucket empty throughout the exercise.

The reviewer needs access to update the pilot stack configuration, create a plan job, read its configuration and plan, and inspect the bucket. A separate operator owns apply and teardown. Scope grants to the development compartment and pilot stack. OCI supports the `target.job.operation` and `target.stack.id` conditions for job access. [Resource Manager IAM reference](https://docs.oracle.com/en-us/iaas/Content/Identity/Reference/resourcemanagerpolicyreference.htm)

## Plan the committed ticket

In the same shell and generated checkout, set `STACK_ID` to the baseline stack OCID. Set `REFERENCE_REPO` to the absolute path of the trusted reference checkout. Review the committed candidate before uploading it. Verify that the diff from the baseline adds only the owner tag in `infra/bucket.tf.json`. Serialize stack updates for this pilot.

```sh
revision=$(git rev-parse HEAD)
git diff pilot-baseline "$revision" -- infra
git archive --format=zip --output="$run_dir/candidate.zip" "$revision:infra"
oci resource-manager stack update --stack-id "$STACK_ID" --config-source "$run_dir/candidate.zip"
job_id=$(oci resource-manager job create-plan-job --stack-id "$STACK_ID" \
  --display-name "owner-tag-$revision" --query 'data.id' --raw-output)
echo "$job_id"
```

Wait until Resource Manager reports **SUCCEEDED** for that job. Run the verifier from the trusted reference checkout and supply the expected owner from the approved ticket. It fetches the job metadata, compares the downloaded configuration with every file in the committed `infra/` tree, and checks the plan JSON. A concurrent upload or a different stack fails the review. If the service is still preparing the downloads, retry with the same job ID. [Create a plan job](https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Tasks/create-job-plan.htm) · [Download job configuration](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/resource-manager/job/get-job-tf-config.html) · [Download a JSON plan](https://docs.oracle.com/en-us/iaas/Content/ResourceManager/Tasks/get-job-tf-plan.htm)

```sh
python3 "$REFERENCE_REPO/review_job.py" --factory . --revision "$revision" \
  --owner cloud-platform --stack-id "$STACK_ID" --job-id "$job_id" \
  --evidence "$run_dir/verified"
```

A passing plan updates one private bucket in place and adds the expected owner while preserving all other attributes. Creations, replacements, deletes, ownership transfers, unrelated updates, unresolved values and drift stop the check. If OCI reports an additional change, inspect the actual before/after values and resolve it separately. A no-op means there is no tag addition to approve. For an already-owned bucket, confirm the owner and close or redirect the ticket. [Terraform JSON plan format](https://developer.hashicorp.com/terraform/internals/json-format)

Keep the private plan and downloaded configuration in the restricted evidence directory. Attach the result from `review.json`, the ticket, candidate SHA and plan job ID to the change review. The pilot can finish at this point. If the team needs to apply the tag, the authorized operator selects the **same reviewed plan job** in Resource Manager and checks the final owner tag.

## Clean up a disposable pilot

In the same stack, confirm the bucket is the dedicated empty pilot and inspect the state. An authorized operator can run a Resource Manager destroy job, verify that the bucket is gone, then delete the stack and retire the branch or temporary worker. A stack that manages other resources requires its own targeted removal change. Follow the team's retention period for private plan evidence and logs.
