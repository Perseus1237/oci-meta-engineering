# Meta engineering on OCI with Codex

Build a factory that other cloud engineering teams can reuse. This starter uses a small infrastructure ticket: add an `owner` tag to a private OCI Object Storage bucket and prove that the Terraform plan changes exactly that tag.

The platform team owns a template, a set of frozen tickets, and an independent plan checker. Each application team gets its own Codex instructions, skill, Terraform configuration, and owner. When a second team needs support for inherited tags, you can replay both versions of the skill and decide whether the improvement belongs in every future factory.

## Try the whole loop locally

From this repository, run these commands with Python 3.8+ and Git on your path:

```sh
python3 -B demo.py
python3 -B -m unittest discover -s tests -v
```

The demo takes a few seconds. It uses the same Python helper that Codex invokes and needs no model login or OCI credentials. The released rule passes **5 of 6** cases. It stops on the analytics team's inherited tag expression. The candidate passes **6 of 6**, preserves existing tags, and earns a template review. The demo writes both team checkouts and a JSON report under the printed `build/demo-…/` path. Its plan fixture comes from a Terraform run against synthetic prior state.

## Give your team a factory

Start from a reviewed release of this repository. Copy [the platform spec](specs/platform.json), set your team name and owner slug, then generate a new checkout. This example uses the supplied spec as written.

```sh
python3 factory.py specs/platform.json ../platform-sandbox
cd ../platform-sandbox
git init -b main
git add .
git commit -m "Start platform bucket factory"
git tag pilot-baseline
git switch -c ticket/add-owner
```

Open this directory in Codex and enter **“Run the ticket in tickets/owner-tag.md using the tag-bucket skill. Show me the diff.”** For a terminal or build worker with an authenticated Codex CLI, the equivalent invocation is:

```sh
mkdir -p .runs
run_dir=$(mktemp -d .runs/owner-tag.XXXXXX)
codex exec --sandbox workspace-write --json - < tickets/owner-tag.md > "$run_dir/events.jsonl"
git status --short
git diff --check
git diff -- infra/bucket.tf.json
```

The expected edit adds `"owner": "cloud-platform"` alongside `"environment": "dev"`. If the worker reports an ownership conflict, the ticket goes back to the factory owner. For a successful edit, review and commit the diff before commissioning an OCI plan. [Codex CLI](https://developers.openai.com/codex/cli/) · [Running Codex non-interactively](https://developers.openai.com/codex/noninteractive/)

## Follow the work through the three tiers

| Tier | Who uses it | What to inspect |
| --- | --- | --- |
| 1 · Run a ticket | Factory owner and Codex | [Ticket](template/tickets/owner-tag.md), [skill](template/.agents/skills/tag-bucket/SKILL.md), and [OCI plan review](docs/oci-pilot.md). A reviewer binds the plan to the exact candidate commit. |
| 2 · Improve a factory | Team that found a recurring failure | [Shared-tags candidate](experiments/shared_tags_rule.py) and [six frozen cases](evals/cases.json). Compare the same inputs, expected edits, and refusal cases across both versions. |
| 3 · Reuse the improvement | Platform template maintainer | [Generator](factory.py), [team specs](specs/), and [promotion walkthrough](docs/promote.md). Every factory records its owner and template fingerprint. |

**Run it on OCI.** The [pilot runbook](docs/oci-pilot.md) covers OCI DevOps Managed Build, an isolated Codex worker, and a Resource Manager plan for an existing bucket. It includes the first-time bootstrap and cleanup paths. The [OCI stack diagram](docs/images/codex-oci-factory-stack.png) shows the larger OKE deployment, including roles for OCIR, Vault, Logging, and Object Storage. The starter implements the local worker, build checks, and Resource Manager review. Teams supply their own tenancy and runtime.

**Adapt it to another ticket.** Start with the acceptance condition your cloud reviewer can observe. Add one representative failure to the frozen cases, change one skill, and test it in a second team checkout. The [meta-engineering diagram](docs/images/meta-engineering.png) illustrates the template-to-factory cycle.
