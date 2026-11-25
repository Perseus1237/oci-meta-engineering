# Working on the OCI solution engineering reference

The primary audience is an OCI solution or sales engineer building customer PoCs. Start with se_factory.py and sales-factory/FACTORY.md. Use sales-factory/QUICKSTART.md for the engineer workflow. Keep the customer deliverable, the customer's acceptance cases, and the shared blueprint distinct in changes. The repository uses fictional engagements and synthetic service responses.

Run `make test` and `make demo` when changing the customer factory. The OCI Managed Build spec runs the same example. For the secondary infrastructure example, factory.py owns the explicit template payload and demo.py runs the bucket-tag replay. Validate Terraform changes against the lock in template/infra/.
