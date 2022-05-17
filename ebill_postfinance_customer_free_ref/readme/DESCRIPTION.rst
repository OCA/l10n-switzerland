This module interconnects the `sale_order_customer_free_ref` from EDI with the `ebill_paynet` module.

The order reference in the XML messge is set with the `customer_order_number` field.
And the `customer_order_free_ref` is added as a <OTHER-REFERENCE> node.
