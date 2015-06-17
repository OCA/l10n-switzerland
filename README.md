[![Build Status](https://travis-ci.org/OCA/l10n-switzerland.svg?branch=8.0)](https://travis-ci.org/OCA/l10n-switzerland)
[![Coverage Status](https://coveralls.io/repos/OCA/l10n-switzerland/badge.svg?branch=8.0)](https://coveralls.io/r/OCA/l10n-switzerland?branch=7.0)


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

Translation Status
------------------
[![Transifex Status](https://www.transifex.com/projects/p/OCA-l10n-switzerland-8-0/chart/image_png)](https://www.transifex.com/projects/p/OCA-l10n-switzerland-8-0)
