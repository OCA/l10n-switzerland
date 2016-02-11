[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/125/9.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-l10n-switzerland-125)
[![Build Status](https://travis-ci.org/OCA/l10n-switzerland.svg?branch=9.0)](https://travis-ci.org/OCA/l10n-switzerland)
[![Coverage Status](https://coveralls.io/repos/OCA/l10n-switzerland/badge.svg?branch=9.0)](https://coveralls.io/r/OCA/l10n-switzerland?branch=7.0)


Odoo/OpenERP Swiss Localization
===============================

This repository hosts official swiss localization provided by OCA.

It extends Odoo/OpenERP to add needed functionnalites to use Odoo/OpenERP in Switzerland.


l10n_ch_bank
------------

Provides the list of swiss banks offices with all relative data as clearing, city, etc.


l10n_ch_zip
-----------

Provides the list of swiss postal ZIP for auto-completion.


l10n_ch_payment_slip
--------------------

Adds ESR/BVR report on invoice. Every ESR/BVR element position can be configured independently by company.
Multiple payment tems on invoices are supported.

It will also allow you to do the import of V11 bank statement files and do an automatical reconciliation.


l10n_ch_base_bank
-----------------

Adds the support of postal account and bank postal account norm.
The partner bank form allows you to input swiss bank account and postal account in a correct manner.


l10n_ch_dta
-----------

Provides support of DTA payment file protocol to generate electronic payment file.
This feature will be depreacted around the end of 2014.


l10n_ch_sepa
------------

Provides support of SEPA/PAIN electronic payment file.
Only credit transfert files are supported.


l10n_ch_scan_bvr
----------------

Allows you to scan the ESR/BVR references and automatically create the proper supplier invoices

l10n_ch_hr_payroll
------------------

Provide Swizerland Payroll Rules.
Allow to specify a LPP range to contract and 2 kinds of children to employee.

[//]: # (addons)
Available addons
----------------
addon | version | summary
--- | --- | ---
[l10n_ch_base_bank](l10n_ch_base_bank/) | 9.0.1.0.0 | Types and number validation for swiss electronic pmnt. DTA, ESR
[l10n_ch_states](l10n_ch_states/) | 9.0.1.0.0 | Switzerland Country States
[l10n_ch_zip](l10n_ch_zip/) | 9.0.2.0.0 | Provides all Swiss postal codes for auto-completion

Unported addons
---------------
addon | version | summary
--- | --- | ---
[l10n_ch_bank](l10n_ch_bank/) | 8.0.9.0.0 (unported) | Banks names, addresses and BIC codes
[l10n_ch_credit_control_payment_slip_report](l10n_ch_credit_control_payment_slip_report/) | 8.0.1.3.0 (unported) | Print BVR/ESR slip related to credit control
[l10n_ch_dta](l10n_ch_dta/) | 8.0.1.0.1 (unported) | Electronic payment file for Swiss bank (DTA)
[l10n_ch_dta_base_transaction_id](l10n_ch_dta_base_transaction_id/) | 1.0 (unported) | Switzerland - Bank Payment File (DTA) Transaction ID Compatibility
[l10n_ch_fds_postfinance](l10n_ch_fds_postfinance/) | 8.0.1.0 (unported) | Download files and import bank statements from FDS
[l10n_ch_fds_upload_dd](l10n_ch_fds_upload_dd/) | 8.0.1.0 (unported) | Upload Direct Debit files to FDS PostFinance
[l10n_ch_fds_upload_sepa](l10n_ch_fds_upload_sepa/) | 8.0.1.0 (unported) | Upload SEPA files to FDS PostFinance
[l10n_ch_hr_payroll](l10n_ch_hr_payroll/) | 8.0.1.0.8 (unported) | Swizerland Payroll Rules
[l10n_ch_import_cresus](l10n_ch_import_cresus/) | 8.0.1.0.0 (unported) | Account Import Cresus
[l10n_ch_payment_slip](l10n_ch_payment_slip/) | 8.0.2.1.0 (unported) | Print ESR/BVR payment slip with your invoices
[l10n_ch_payment_slip_account_statement_base_completion](l10n_ch_payment_slip_account_statement_base_completion/) | 1.0 (unported) | Switzerland - BVR/ESR Bank statement Completion
[l10n_ch_payment_slip_base_transaction_id](l10n_ch_payment_slip_base_transaction_id/) | 1.0 (unported) | Switzerland - BVR/ESR Transaction ID Compatibility
[l10n_ch_payment_slip_layouts](l10n_ch_payment_slip_layouts/) | 8.0.0.1.0 (unported) | Add new BVR/ESR payment slip layouts like invoice with slip on same document
[l10n_ch_payment_slip_voucher](l10n_ch_payment_slip_voucher/) | 8.0.1.0.0 (unported) | Import Payment Slip (BVR/ESR) into vouchers
[l10n_ch_scan_bvr](l10n_ch_scan_bvr/) | 1.0 (unported) | Switzerland - Scan ESR/BVR to create invoices
[l10n_ch_sepa](l10n_ch_sepa/) | 8.0.1.0.0 (unported) | Generate pain.001 Credit Transfert Files for your payments

[//]: # (end addons)

Translation Status
------------------
[![Transifex Status](https://www.transifex.com/projects/p/OCA-l10n-switzerland-9-0/chart/image_png)](https://www.transifex.com/projects/p/OCA-l10n-switzerland-9-0)
