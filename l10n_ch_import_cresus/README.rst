.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Module name
===========

This module add the ability to import CSV file from Cresus software (www.cresus.ch) 

Configuration
=============



Usage
=====
In order to import your Cresus Salaires.txt 
file you must complete the following requirements : 
    * The accounts, analytical accounts used in the Cresus
      file must be previously created into Odoo
    * The date of the entry will determine the period used
      in Odoo, so please ensure the period is created already.
    * If the Cresus file uses VAT codes (i.e: IPI), 
      please make sure you have indicated this code in the
      related Odoo tax (field : Cresus tax name).
      Warning, the Odoo tax must be 'tax included'.
      If the tax does not exist you have to create it.
    * All PL accounts must have a deferral method = 'none'
        (meaning: no balance brought forward in the new fiscal year) and all
         Balance sheet account must have a deferral method = 'balance'.)


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

* Vincent renaville <vincen.renaville@camptocamp.com>

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
