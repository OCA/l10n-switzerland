.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl
   :alt: License: AGPL-3

=============
Import Cresus
=============

This module add the ability to import CSV file from Cresus software (www.cresus.ch)

Installation
============

Nothing special to install this module. Just click on install in module list.

Configuration
=============

No configuration is required to use this module.

Usage
=====
In order to import your 'Cresus Salaires' .txt file you must complete the following requirements :

* The accounts, analytical accounts used in the Cresus file must be previously created into Odoo.

* If the Cresus file uses VAT codes (i.e: IPI), please make sure you have indicated this code in the related Odoo tax (field : Cresus tax name). Warning, the Odoo tax must be 'tax included'. If the tax does not exist you have to create it.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/125/10.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/{project_repo}/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smash it by providing detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Vincent Renaville <vincent.renaville@camptocamp.com>
* Louis Bettens <lbe@open-net.ch>

Do not contact contributors directly about support or help with technical issues.

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
