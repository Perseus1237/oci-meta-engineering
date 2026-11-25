# Quickstart for OCI solution engineers

**Goal:** Leave with an AI factory you can use on a customer engagement. The factory takes a customer brief, commissions Codex with a work order, runs independent acceptance checks, and produces a PoC the customer can try. You own the customer conversation and the decision to reuse a change.

Use Python 3.8+ for the offline walkthrough. Install and authenticate the Codex CLI when you reach the live build. The invoice PoC's live service path additionally needs an OCI CLI profile, an approved sample invoice in Object Storage and access to Document Understanding in that region. [Codex CLI](https://developers.openai.com/codex/cli/)

### 1. Watch a factory earn a reusable improvement

From the directory containing `se_factory.py`, run:

```sh
python3 -B se_factory.py demo
```

Open the printed Harbor HTML queue. Compare the two PO numbers and their source pages. In `replay.json`, find the initial failure for `two-po-numbers`, then the candidate result on the same input. Finally inspect Cedar's queue under `reuse/cedar/output/`. Cedar benefits from the fix for a different field.

### 2. Create your own factory

Run this from the reference checkout. If you are reading the README inside the new factory, continue to step 3.

```sh
python3 se_factory.py new-factory ../my-se-factory
cd ../my-se-factory
git init
git add .
git commit -m "Start solution engineering factory"
```

The standalone factory contains its own CLI, build order, grader, invoice blueprint and fictional examples. New engagements belong in `sales-factory/engagements/`, which the generated factory excludes from Git by default. Put actual customer work in the customer-approved repository or workspace.

### 3. Capture the next customer's decision

For an invoice engagement, copy the nearest example. Each new destination in this guide should be unused.

```sh
mkdir -p sales-factory/engagements
cp -R sales-factory/examples/harbor sales-factory/engagements/invoice-pilot
```

For a different solution, generate a fresh blueprint and first engagement:

```sh
python3 se_factory.py new-pattern service-request-routing
```

This creates `sales-factory/blueprints/service-request-routing/solution.py` and `sales-factory/engagements/service-request-routing-pilot/`. The scaffold includes a fictional routing example. Replace it with the customer's own decision. In discovery, ask:

| Ask the customer | Record it in the engagement |
| --- | --- |
| Who makes which decision today? What should they be able to do in the demo? | `brief.json` — user, decision, deliverable, settings |
| What should a straightforward input produce? What should go to a human? | Synthetic or approved inputs in `samples/` |
| What exact output would make you accept each example? | `acceptance.json` — one case ID, sample filename and expected fields per example |
| Which OCI service will supply the input? What will we measure when we connect it? | Add `oci_service` and `live_validation` to the brief. Discuss identity and data location with the customer. |

A useful first case is concrete. For example, a damaged-shipment request should produce `{"queue":"claims"}`. The scaffold also includes a routine delivery question and an ambiguous request. Replace or confirm their expected outcomes with the customer. A factory-level Codex prompt you can use is **“Read this discovery brief. Draft three synthetic acceptance examples, including an ambiguous case. List the decisions I need the customer to confirm.”**

### 4. Commission Codex and inspect the handoff

For the new routing pattern, run the scaffold once before building. Its unimplemented workflow should return **HOLD** and a case-level diagnostic. That shows the acceptance checks can detect missing behavior.

```sh
python3 se_factory.py run sales-factory/engagements/service-request-routing-pilot build/before
```

After confirming the cases, run the live build in a fresh workspace:

```sh
python3 se_factory.py run sales-factory/engagements/service-request-routing-pilot \
  build/customer-poc --codex
```

The CLI materializes the approved inputs, invokes Codex with `work-order.md`, then executes the factory's grader against the **original** brief, samples and expected outputs. Open `output/acceptance-report.json`, inspect the implementation and follow the demo command in the agent's `HANDOFF.md`. The JSONL trace is under `.runs/`. A failing case, changed evidence or an unavailable builder stops the run. Use a new destination for each attempt so you can compare results.

For a credential-free run of a complete blueprint, use:

```sh
python3 se_factory.py run sales-factory/engagements/invoice-pilot build/invoice-demo
```

Open `build/invoice-demo/output/review.html`. To connect real OCI extraction, follow the Object Storage analysis command in that generated project's README. Keep fixture-routing results and measured live accuracy separate in the customer handoff.

### 5. Teach the factory what the engagement proved

Keep the customer's queue names, examples, thresholds and tenancy settings in the engagement. Extract a reusable behavior into a **candidate copy** of the blueprint. For the routing example, compare the built `solution.py` with the starter. Move the reusable implementation and any helper files into the candidate, listing its payload in `blueprint.json`. Put routing policy that varies by customer in `brief.json`. A blueprint can declare a Python `demo_entry` from its payload to generate a customer artifact on a successful run.

Practice the promotion gate with the included invoice candidate:

```sh
python3 se_factory.py replay sales-factory/blueprints/invoice-intake \
  sales-factory/examples/juniper sales-factory/examples/harbor sales-factory/examples/cedar
```

Use the same command with your candidate directory and your previous and new engagement directories. Inspect the reports from the fresh workspaces. When they pass and another SE has reviewed the change, merge the candidate into the shared blueprint and tag the factory release. Commission the next PoC from that tag. That is the reusable unit your practice can carry from customer to customer.
