# Operate the solution engineering factory

The SE owns discovery, customer acceptance and release decisions. Codex can help at each stage. The reference can run these roles in a single session.

| Role | Input | Output and review point |
| --- | --- | --- |
| Discovery partner | Customer's workflow, target user and desired decision | Draft a brief and synthetic examples. The SE confirms expected outcomes with the customer before the build. |
| Builder | Approved brief, blueprint, work-order.md and example inputs | Work inside the generated customer checkout. Produce runnable code, execute local checks and write HANDOFF.md. |
| Evaluator | Candidate program and the original engagement evidence | Run the factory's independent check.py. Preserve expected outcomes while investigating failures. |
| Blueprint maintainer | A new failure and a generalizable fix | Replay the proposed blueprint on earlier engagements. The SE reviews the change before adding it to the shared practice. |

The public interface of a blueprint is `solve(document, brief)` in `solution.py`. Return a JSON object. The grader compares the fields named in each case's `expect` object, including exact list contents. Additional fields can carry source evidence for a customer's UI. Keep customer names and environment values in the brief.

Use `python3 se_factory.py new-pattern NAME` for a new problem family. Use `run ENGAGEMENT DESTINATION --codex` for an agent build and `replay BLUEPRINT ENGAGEMENT ...` for promotion evidence. The evaluator runs local candidate code. Run live builds and external candidate code in the practice's isolated development environment. Keep OCI credentials for live validation with the engagement owner.
