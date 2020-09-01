![Licence](https://img.shields.io/badge/licence-AGPL--3-blue.svg)
[![Runbot Status](https://runbot.odoo-community.org/runbot/badge/flat/125/13.0.svg)](https://runbot.odoo-community.org/runbot/repo/github-com-oca-l10n-switzerland-125)
[![Build Status](https://travis-ci.org/OCA/l10n-switzerland.svg?branch=13.0)](https://travis-ci.org/OCA/l10n-switzerland)
[![Coverage Status](https://coveralls.io/repos/OCA/l10n-switzerland/badge.svg?branch=13.0)](https://coveralls.io/r/OCA/l10n-switzerland?branch=13.0)


Odoo Swiss Localization :switzerland:
=====================================

This repository hosts official Swiss localization provided by the OCA.

It extends Odoo to add needed functionalities to use Odoo in Switzerland.


:new: ebill_paynet
------------------

Send eBills, digital invoices, through the e-billing platform paynet (www.ebill.ch) to your customers.

PR in review state: https://github.com/OCA/l10n-switzerland/pull/551

:new: l10n_ch_qr_bill_scan
--------------------------

To use a scanner on the QR-bills' QR code (www.qr-bill.ch) and create the proper supplier invoices

PR in review state: https://github.com/OCA/l10n-switzerland/pull/553


l10n_ch_bank
------------

Provides the list of Swiss banks offices with all relative data as clearing, city, etc.


l10n_ch_zip
-----------

Provides the list of Swiss postal ZIPs for auto-completion.


l10n_ch_base_bank
-----------------

Adds the support of postal account and bank postal account norm.
The partner bank form allows you to input Swiss bank account and postal account in a correct manner.

:bulb: Since v13 this module becomes highly optional, most of its feature have be push into Odoo core


l10n_ch_pain_credit_transfert
-----------------------------

Provides support of SEPA/PAIN electronic payment file.


l10n_ch_hr_payroll
------------------

Provides Swiss Payroll Rules.
Allows to specify a LPP range to contract and 2 kinds of children to employees.

l10n_ch_import_cresus
---------------------

This module add the ability to import CSV file from Crésus software (www.cresus.ch)

l10n_ch_import_winbiz
---------------------

Allows to import accounting from WinBIZ software (www.winbiz.ch) using Excel or XML format.


l10n_ch_payment_slip
--------------------

:ghost: DEPRECATED :ghost:

ISR are now deprecated by the QR-Bill while still valid till 2022 it is wise to consider using QR-bills instead
The QR-bills are available in Odoo core.

Adds ISR (PVR/BVR/ESR) report on invoice. Every ISR element position can be configured independently by company.
Multiple payment terms on invoices are supported.


Translation Status
------------------
[![Transifex Status](https://www.transifex.com/projects/p/OCA-l10n-switzerland-13-0/chart/image_png)](https://www.transifex.com/projects/p/OCA-l10n-switzerland-13-0)
