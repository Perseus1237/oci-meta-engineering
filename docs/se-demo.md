# Show the AI factory in five minutes

**Audience:** OCI solution and sales engineers who build customer proofs of concept. **Opening line:** “Suppose you finish a successful PoC on Friday. When a different customer asks for something similar on Monday, what exactly can the next engineer reuse?”

Run `make demo` in the reference checkout and keep the printed Harbor report and replay JSON handy.

| Time | Show | Say or ask |
| --- | --- | --- |
| 0:00–1:00 | Harbor's brief and three acceptance cases | “The AP lead needs a review queue. One example contains two different purchase orders. Before we build, what should the clerk see?” |
| 1:00–2:00 | The generated Harbor workspace, work order and HTML queue | “This is the customer deliverable. The brief supplies the business rule. The blueprint supplies the application. The same workspace is where Codex works when we run the live build.” Point to both readings and their pages. |
| 2:00–3:00 | The initial and candidate rows in the replay | “The first customer accepted the original rule. At Harbor, picking the higher-confidence reading sent a conflicting invoice to data entry. We can reproduce that error and verify the fix without changing either customer's expected outcomes.” |
| 3:00–4:00 | Cedar's brief and `reuse/cedar/output/review.html` | “Cedar asks about invoice IDs. Watch the same improved rule catch that conflict with no new routing code. Which part of your last PoC would have helped another SE this way?” |
| 4:00–5:00 | `new-factory` and `new-pattern` in the quickstart | “Pick your next engagement. Give the factory one customer decision, one ordinary case, and one case that needs a person. Now we have something concrete to commission Codex to build.” |

The runnable demo uses completed blueprint revisions and synthetic OCI responses so everyone can replay the same failure. To demonstrate the model building code, follow the live `--codex` path on the unimplemented routing scaffold. To demonstrate the cloud service, run the generated invoice project's OCI command with an approved document. [SE quickstart](../sales-factory/QUICKSTART.md) · [Harbor brief](../sales-factory/examples/harbor/brief.json) · [Harbor cases](../sales-factory/examples/harbor/acceptance.json)
