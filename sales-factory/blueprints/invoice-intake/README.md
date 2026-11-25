# Invoice intake PoC

The accounts-payable reviewer gets a queue of invoices ready for data entry and invoices needing a closer look. Open brief.json for the customer-specific fields and confidence threshold. The decision is an intake suggestion. Payment authorization stays with the customer's existing process.

Run `python3 -B check.py` to replay the customer's examples. Run `python3 -B solution.py` and open `output/review.html` to inspect the evidence behind each decision. The included samples are synthetic extraction responses. For an approved invoice already in OCI Object Storage, use an authenticated OCI CLI in its region:

```sh
mkdir -p output
oci ai-document analyze-document-result analyze-document-object-storage-document-details \
  --compartment-id "$COMPARTMENT_OCID" --document-namespace-name "$NAMESPACE" \
  --document-bucket-name "$BUCKET" --document-object-name "$OBJECT_NAME" \
  --document-type INVOICE --features '[{"featureType":"KEY_VALUE_EXTRACTION"}]' \
  --output json > output/analysis.json && \
  python3 -B solution.py output/analysis.json --out output/live-review.html
```

Use a principal authorized for Document Understanding analysis and the chosen object. Keep live inputs and output in the engagement's private workspace. Compare extracted values and routing with customer-labeled examples before reporting live results. [Oracle invoice extraction](https://docs.oracle.com/en-us/iaas/Content/document-understanding/using/pre_trained_doc_keyvalue_invoice.htm) · [OCI CLI operation](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/ai-document/analyze-document-result/analyze-document-object-storage-document-details.html)
