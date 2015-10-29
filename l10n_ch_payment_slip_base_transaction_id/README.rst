Swiss BVR/ESR Transaction ID Compatibility
==========================================

Link module between the Swiss localization BVR/ESR module
(l10n_ch_payment_slip) and the module adding a transaction ID
field (base_transaction_id).

When an invoice has a transaction ID, no BVR reference should be generated
because the reconciliation should be done with the transaction ID, not
a new reference.

This module is needed if you use the Swiss localization module and the
bank-statement-reconcile project in the banking addons
(https://github.com/oca/bank-statement-reconcile).
