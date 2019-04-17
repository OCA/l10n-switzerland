This addon allows you to print the ISR report Using Qweb report.

ISR is called:
- PVR in italian
- BVR in french
- ESR in german

The ISR is grenerated as an image and is availabe in a fields
of the `l10n_ch.payment_slip` Model.

This module also adds transaction_ref field on entries in order to manage
reconciliation in multi payment context (unique reference needed on
account.move.line). Many ISR can now be printed from one invoice for each
payment terms.
