The ISR is created each time an invoice is validated.
To modify it you have to cancel it and reconfirm the invoice.

You can also activate "Save as attachement" for ISR prints your invoice.
To do so, edit the ir.actions.report `Payment Slip` with the template
name `l10n_ch_payment_slip.one_slip_per_page_from_invoice`.

To import v11, the feature has been moved in module `l10n_ch_import_isr_v11`
