# Build the customer's proof of concept

Read brief.json, acceptance.json, and the synthetic examples in samples/. Summarize the end user's decision and the OCI service boundary. Implement solve(document, brief) in solution.py and a runnable way for the customer to inspect its output. Reuse the blueprint where it fits.

If the brief names an OCI service, implement or reuse its input adapter and keep a fixture path for replay. Document what identity and inputs the live path needs. Run python3 -B check.py. Address implementation failures and replay the same cases. Keep the acceptance criteria fixed for this run. Write HANDOFF.md with the demo command, observed results, fixture versus live-service coverage, and one candidate for reuse across engagements. Surface any decision that needs the customer.
