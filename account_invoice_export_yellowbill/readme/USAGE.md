The payload is built by the `account.invoice.yellowbill` model. The caller
passes the identifiers of its own eBill contract:

```python
payload = self.env["account.invoice.yellowbill"]._export_invoice(
    invoice,
    biller_id="99999999999999999",
    ebill_account_id="11111111111111111",
    transaction_id="240101120000-INV0001",
    pdf_data=base64_encoded_pdf,
)
self.env["account.invoice.yellowbill"]._validate_payload(payload)
```
