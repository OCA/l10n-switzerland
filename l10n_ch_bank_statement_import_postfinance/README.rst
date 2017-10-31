.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==================================
Import Postfinance bank statements
==================================

This module allows you to import Postfinance .tar.gz bank statements
including .xml statements and pictures of the ESR payment slips.
It currently supports the following file formats :

* XML format from Postfinance S.A.

Warning : this module requires the python library 'xlrd' and 'wand'.

Installation
============

To install this module, you need to add the statement import module into your
addons path, because it's based on the CAMT import module.
https://github.com/OCA/bank-statement-import

Configuration
=============

To configure this module, you need to ensure you have a bank account related to
your company that corresponds to imported statement.


If the statement is not in the same currency that company please ensure that
both journal and account have the currency (or secondary currency) properly
set to statement currency.

Usage
=====

To use this module, you need to:

#. Go to *Accounting* dashboard.
#. Click on *Import statement* from any of the bank journals.
#. Select a .tar.gz file from Postfinance.
#. Press *Import*.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/174/9.0

Bug Tracker
===========

Bugs are tracked on
`GitHub Issues <https://github.com/OCA/l10n-switzerland/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and
welcomed feedback.

Credits
=======

Contributors
------------    

* Nicolas Bessi <nicolas.bessi@camptocamp.com>
* Steve Ferry <steve.ferry1992@gmail.com>
* Emanuel Cino <ecino@compassion.ch>
* Emmanuel Mathier <emmanuel.mathier@gmail.com>

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
