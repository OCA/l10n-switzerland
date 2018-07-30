![Licence](https://img.shields.io/badge/licence-AGPL--3-blue.svg)
[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/125/11.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-l10n-switzerland-125)
[![Build Status](https://travis-ci.org/OCA/l10n-switzerland.svg?branch=11.0)](https://travis-ci.org/OCA/l10n-switzerland)
[![Coverage Status](https://coveralls.io/repos/OCA/l10n-switzerland/badge.svg?branch=11.0)](https://coveralls.io/r/OCA/l10n-switzerland?branch=11.0)


Odoo/OpenERP Swiss Localization
===============================

This repository hosts official Swiss localization provided by the OCA.

It extends Odoo/OpenERP to add needed functionalities to use Odoo/OpenERP in Switzerland.


l10n_ch_bank
------------

Provides the list of Swiss banks offices with all relative data as clearing, city, etc.


l10n_ch_zip
-----------

Provides the list of Swiss postal ZIPs for auto-completion.


l10n_ch_payment_slip
--------------------

Adds ISR (PVR/BVR/ESR) report on invoice. Every ISR element position can be configured independently by company.
Multiple payment terms on invoices are supported.

It will also allow you to do the import of V11 bank statement files and do an automatic reconciliation.


l10n_ch_base_bank
-----------------

Adds the support of postal account and bank postal account norm.
The partner bank form allows you to input Swiss bank account and postal account in a correct manner.


l10n_ch_dta
-----------

Provides support of DTA payment file protocol to generate electronic payment file.
This feature will be deprecated around the end of 2016.


l10n_ch_pain_credit_transfert
-----------------------------

Provides support of SEPA/PAIN electronic payment file.


(replaces former l10n_ch_sepa module)


l10n_ch_scan_bvr
----------------

Allows you to scan the ISR references and automatically create the proper supplier invoices

l10n_ch_hr_payroll
------------------

Provides Swiss Payroll Rules.
Allows to specify a LPP range to contract and 2 kinds of children to employees.

l10n_ch_import_cresus
---------------------

This module add the ability to import CSV file from Crésus software (www.cresus.ch)

l10n_cd_import_winbiz
---------------------

Allows to import accounting from WinBIZ software (www.winbiz.ch) using Excel or XML format.



Translation Status
------------------
[![Transifex Status](https://www.transifex.com/projects/p/OCA-l10n-switzerland-11-0/chart/image_png)](https://www.transifex.com/projects/p/OCA-l10n-switzerland-11-0)
