Backport of Odoo 13.0 core module

Added a QR-IBAN field on bank account.
If this field is empty, but the bank account number itself is a valid QR-IBAN number, it will still be used as QR-IBAN as before.  
But if you fill in the new QR-IBAN field, that one will be used as the QR-IBAN.  This should help for reconciliation as 
on the bank statements, the old IBAN code is still used.  
