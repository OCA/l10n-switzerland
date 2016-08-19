.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

=============
Import Crésus
=============

This module add the ability to import CSV file from Crésus software (www.cresus.ch)

Installation
============

Nothing special to install this module. Just click on install in module list.

Configuration
=============

No configuration is required to use this module.

Usage
=====
In order to import your 'Crésus Salaires' .txt file you must complete the following requirements : 

* The accounts, analytical accounts used in the Crésus file must be previously created into Odoo.

* If the Crésus file uses VAT codes (i.e: IPI), please make sure you have indicated this code in the related Odoo tax (field : Crésus tax name). Warning, the Odoo tax must be 'tax included'. If the tax does not exist you have to create it.

Known issues / Roadmap
======================

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-switzerland/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback
`here <https://github.com/OCA/l10n-switzerland/issues/new?body=module:%20l10n_ch_import_cresus%0Aversion:%208.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Vincent Renaville <vincent.renaville@camptocamp.com>
* Louis Bettens <lbe@open-net.ch>

Maintainer
----------

.. image:: http://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: http://odoo-community.org

This module is maintained by the OCA.

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

To contribute to this module, please visit http://odoo-community.org.
