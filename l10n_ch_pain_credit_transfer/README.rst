.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=======================================
Switzerland - ISO 20022 credit transfer
=======================================

This module adds support for *pain.001.001.03.ch.02* which is used for ISO 20022 credit transfers in Switzerland (SEPA or not SEPA).

It implements the guidelines for `ISO 20022 credit transfers <http://www.six-interbank-clearing.com/dam/downloads/fr/standardization/iso/swiss-recommendations/implementation_guidelines_ct.pdf>`_ published by SIX Interbank Clearing.

Configuration
=============

In the menu *Accounting > Configuration > Management > Payment Methods*,
select the payment method that has the code *sepa_credit_transfer* and
set the *PAIN Version* to *pain.001.001.03.ch.02 (credit transfer in Switzerland)*.

Usage
=====

On the payment order, you will see a new computed boolean field named
*BVR* which shows if the payment order is BVR or not.

This module doesn't modify the standard usage of the modules
*account_payment_order* and *account_banking_sepa_credit_transfer*.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/125/9.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/l10n-switzerland/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Contributors
------------

* Alexis de Lattre <alexis.delattre@akretion.com>
* Denis Leemann <denis.leemann@camptocamp.com>

Maintainer
----------

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit https://odoo-community.org.
