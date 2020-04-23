Definintion of a specific grouping rule for ISR payments

This module is recommended if you use SEPA pain files.

Usually to reduce payment fees, you want to group
Vendor Bills by supplier in your payments.
In case of Swiss SEPA with ISR we want to keep a single transaction per ISR
and the additionnal fees per payment doesn't apply.

Moreover grouping payments usually concatenate the Vendor references
and make it more difficult for your suppliers to reconciliate
your payments as multiple ISR references concatenated are not supported
in SEPA file format.

This module checks if a payment is an ISR payment:

ISR: never group payments
other: standard grouping
