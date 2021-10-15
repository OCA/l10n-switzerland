Create a service
================

To create a service you need to be registred with SIXT Paynet service. Then the configuration of the service can be done in `Accounting - Configuration - Payments - Paynet Service`

Configure the customers
=======================

A customer that wants to receive his invoices through Paynet will also need to register with the service.
In Odoo to enable the sending of invoices for a specific customer through Paynet, the transmit method must be set accordingly for that customer. This is done on the customer form in the tab `Sales & Purchases` section `Sales`.

Configure the contracts
=======================

The contracts specific to e-billing are located in `Accounting - Customers - eBill Payment Contract`
Although the Paynet system allows for automatic exchange of contract registration and status changes, this automation is not yet implemented.
To be active a contract needs to be in the state `Open` and it's start/end dates to be valid.
