This addon allows you to print the ESR/BVR report Using Qweb report.

The ESR/BVR is grenerated as an image and is availabe in a fields
of the `l10n_ch.payment_slip` Model.

The ESR/BVR is created each time an invoice is validated.
To modify it you have to cancel it and reconfirm the invoice.

You can adjust the print out of ESR/BVR, which depend on each printer,
for every company in the "BVR Data" tab.

This is especialy useful when using pre-printed paper.
An option also allow you to print the ESR/BVR in background when using
white paper.

This module will also allows you to import v11 files provided
by financial institute into a bank statement

To do so, use the wizard provided in bank statement.

This module also adds transaction_ref field on entries in order to manage
reconciliation in multi payment context (unique reference needed on
account.move.line). Many BVR can now be printed from on invoice for each
payment terms.
