.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3


Scan ESR/BVR to create supplier invoices
========================================

This module works with C-channel or other OCR scanner.

It helps you to create an invoice directly from the ESR/BVR Code.

Find the menu entry called "Scan BVR" under Accounting -> Supplier.
It open a popup from which you can scan the ESR/BVR number.

It'll recognize the needed information and create an invoice for the right supplier.

If you have completed the field "Default product supplier invoice" on the concerned supplier, it'll create a line with the proper amount and the given product.

It currently supports BVR and BVR+

Installation
============

To install this module, you need to:

* download and install manually
* or directly install it over Odoo-Apps

History
-------

* First version: 2009/Nicolas Bessi and Vincent Renaville (CamptoCamp).
* Then ported to Odoo V7 by Vincent Renaville(@vrenaville).
* Revised by @hurrinico to port it to V8 (feb. of 2015).

V1.8: 2015-09-07/Cyp (Open-Net Sarl)
    * Code reformatted to comply to OCA and Odoo's new standards as well as to the new API system
    * Removed the dependency to ``l10n_ch_payment_slip``
    * Added missing translations    


Dependencies
============

The module ``l10n_ch`` is required, available here: 
https://github.com/OCA/l10n-switzerland


Configuration
=============

To configure this module, you need to:

* do nothing


Usage
=====

To use this module, you need to:

* Optionnally define a product in any supplier's form you may use
* Open the wizard: " Accounting > BVR Scan"

For further information, please visit:

* https://www.odoo.com/forum/help-1


Known issues / Roadmap
======================

* actually there are no issues known


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-switzerland/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/l10n-switzerland/issues/new?body=module:%20l10n_ch_zip%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.
`here <https://github.com/OCA/l10n-switzerland/issues/new?body=module:%20l10n_ch_scan_bvr%0Aversion:%208.0.1.8%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Contributors
============

* Yvon-Philippe Crittin <cyp@open-net.ch>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
