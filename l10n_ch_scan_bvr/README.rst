.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

========================================
Scan ESR/BVR to create supplier invoices
========================================

This module works with C-channel or other OCR scanner.

It helps you to create an invoice directly from the ESR/BVR Code.
Find the menu entry called "Scan BVR" under Accounting -> Supplier.
It opens a popup from which you can scan the ESR/BVR number.
It'll recognize the needed information and create an
invoice for the right supplier.

If you have completed the field "Default product supplier invoice"
on the concerned supplier,
it'll create a line with the proper amount and the given product.

It currently supports BVR and BVR+

Usage
=====

To use this module, you need to:

* Optionally define a product in any supplier's form you may use
* Open the wizard: " Accounting > BVR Scan"

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/125/9.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/
l10n-switzerland/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback.


Credits
=======

Contributors
------------

* Vincent Renaville <vincent.renaville@camptocamp.com>
* Yannick Vaucher <yannick.vaucher@camptocamp.com>
* Joël Grand-Guillaume <joel.grandguillaume@camptocamp.com>
* Nicolas Bessi <nicolas.bessi@camptocamp.com>
* Moises Lopez <moylop260@vauxoo.com>
* Alexandre Fayolle <alexandre.fayolle@camptocamp.com>
* César Andrés Sanchez <cesar-andres.sanchez@braintec-group.com>
* Nicola Malcontenti <nicola.malcontenti@agilebg.com>
* Alex Comba <alex.comba@agilebg.com>
* Álvaro Estébanez López <alvaro.estebanez@braintec-group.com>

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
