.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Swiss bank statements import
============================

 This module adds several import types to the module
 account_statement_base_import, in order to read swiss bank statements.
 It currently supports the following file formats :

 * .v11, .esr, .bvr formats (ESR standard) for records of type 3
   (type 4 is ready to be implemented)
 * .g11 format from Postfinance S.A. for Direct Debit records of type 2
 * XML format from Postfinance S.A.
 * .csv format from Raiffeisen Bank
 * .csv format from UBS Bank [CH-FR]

 Warning : this module requires the python library 'xlrd'.


Installation
============

To install this module, you need to add the statment import module into your addons path
https://github.com/OCA/bank-statement-import

Configuration
=============

To configure this module, you need to ensure you have a bank account related to
your company that corresponds to imported statement.


If the statement is not in the same currency that company please ensure that
both journal and account have the currency (or secondary currency) properly
set to statement currency.

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

To contribute to this module, please visit http://odoo-community.org.
