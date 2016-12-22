.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=======================
Switzerland - Bank type
=======================

This addons will add different bank types required by specific swiss electronic
payment like DTA and ESR. It allows to manage both Post and Bank systems.

It'll perform some validation when entring bank account number or ESR number
in invoice and add some Swiss specific fields on bank.

This module is required if you want to use electronic payment in Switzerland.

Usage
=====

Account type will be discovered authomatically.

* For IBAN accounts fill account number with IBAN.
* For Postal account fill account number with postal account number in IBAN, 9 digits or 6 digits format (ex. 01-23456-1 or 12345).

Entering a postal number of 9 or 6 digits will auto-complete the bank with PostFinance. (You might create it if you haven't installed `l10n_ch_bank`)

* For bank account for BVR, select the bank and fill the CCP field in bank, optionally fill the account number with bank number.


.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/125/10.0


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/
l10n-switzerland/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback `here <https://github.com/OCA/
l10n-switzerland/issues/new?body=module:%20
l10n_ch_base_bank%0Aversion:%20
9.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Nicolas Bessi (Camptocamp)
* Vincent Renaville <vincent.renaville@camptocamp.com>
* Joël Grand-Guillaume <joel.grandguillaume@camptocamp.com>
* Guewen Baconnier <guewen.baconnier@camptocamp.com>
* Paul Catinean <paulcatinean@gmail.com>
* Yannick Vaucher <yannick.vaucher@camptocamp.com>
* Akim Juillerat <akim.juillerat@camptocamp.com>

Financial contributors
----------------------

Hasa SA, Open Net SA, Prisme Solutions Informatique SA, Quod SA

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
