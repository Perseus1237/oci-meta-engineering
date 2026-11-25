# Build an AI factory for OCI customer PoCs

An OCI solution engineer walks out of customer discovery with a brief. What happens next? In this reference, the engineer runs a factory that gives Codex the brief, a reusable solution blueprint, and examples of what the customer will accept. The factory produces a runnable PoC and evidence the engineer can take back to the customer. A lesson from one engagement can then improve the blueprint used on the next.

**Start here to build your own factory:** [SE quickstart](sales-factory/QUICKSTART.md). **To show the pattern to a room of engineers:** [five-minute demo guide](docs/se-demo.md).

## See the pattern in action

Run from this checkout with Python 3.8 or later. The walkthrough uses fictional customers and synthetic OCI extraction results. It runs offline.

```sh
python3 -B se_factory.py demo
```

Open the Harbor invoice queue at the path the command prints. One document contains **PO-732 on page 1 and PO-723 on page 2**. Both readings have high confidence. The original PoC picked the higher score and sent the invoice to data entry. Harbor's reviewer wanted to see both readings and make the call.

| Customer engagement | What the SE learns | What the factory demonstrates |
| --- | --- | --- |
| Juniper Wholesale | A clerk needs an invoice ID, vendor and total before entry. | The first PoC handles a complete invoice and a faded total. |
| Harbor Field Services | Purchase order is required. Two different readings must go to a person. | Replay exposes a wrong routing decision. The improved blueprint catches conflicting readings of any required field. Juniper's original cases still pass. |
| Cedar Repairs | The bookkeeper cares about conflicting **invoice IDs**. | A fresh PoC inherits the improvement. Cedar supplies its own brief and cases. Its SE writes no new routing code. |

## What makes this an AI factory?

| Step | What the engineer or Codex does | Artifact to inspect |
| --- | --- | --- |
| Specify | An SE and customer agree on a user, a decision, sample inputs and observable outcomes. | [Harbor brief](sales-factory/examples/harbor/brief.json) · [Acceptance examples](sales-factory/examples/harbor/acceptance.json) |
| Commission and build | The factory creates an isolated customer workspace from a blueprint. In live mode, Codex reads a build order, implements the PoC, runs checks and writes the handoff. | [Factory CLI](se_factory.py) · [Codex work order](sales-factory/common/work-order.md) |
| Demonstrate and verify | The factory grades the generated solution against the original engagement inputs. The customer sees the queue and the evidence behind each decision. | [Independent grader](sales-factory/common/check.py) · [OCI service path](sales-factory/blueprints/invoice-intake/README.md) |
| Improve and reuse | The SE turns a failure into a reusable rule, replays earlier engagements, and reviews a blueprint release. The next customer gets that release. | [Original selection rule](sales-factory/history/invoice-intake-initial.py) · [Improved rule](sales-factory/blueprints/invoice-intake/policy.py) |

## Start a factory for your practice

```sh
python3 se_factory.py new-factory ../my-se-factory
cd ../my-se-factory
python3 se_factory.py new-pattern service-request-routing
```

You now own a standalone factory, a blueprint scaffold and a first pilot engagement. Replace the discovery examples with the customer-agreed cases. Run the following with an installed, authenticated Codex CLI:

```sh
python3 se_factory.py run sales-factory/engagements/service-request-routing-pilot \
  build/first-customer --codex
```

The quickstart walks through the first failing acceptance case, the build, the customer demo, and promotion into your practice blueprint. For invoice intake, the generated PoC also accepts responses from a live OCI Document Understanding request on an Object Storage file. The offline replay measures routing against agreed examples. Measure extraction quality separately on customer-labeled documents. [SE quickstart](sales-factory/QUICKSTART.md) · [OCI invoice key-value extraction](https://docs.oracle.com/en-us/iaas/Content/document-understanding/using/pre_trained_doc_keyvalue_invoice.htm)

Run `make test` for the repository checks. The original bucket-tag example is available as a smaller infrastructure exercise. [Infrastructure example](INFRA-EXAMPLE.md)
