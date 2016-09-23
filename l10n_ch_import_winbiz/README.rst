.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

l10n_ch_import_winbiz
=====================

Allows to import accounting from WinBIZ software (www.winbiz.ch) using Excel or XML format.

Installation
============

This module can be installed from the web interface. It depends on the python
package xlrd though.


Configuration
=============

No configuration is required to use this module.


Usage
=====
In order to import your Excel Spreadsheet you must complete the following requirements:

* The accounts used in the WinBIZ file must have been previously created into
  Odoo

* The WinBIZ journals must also exist and have their WinBIZ one-letter codes
  filled in into the ad-hoc field

* The taxes must exist. They will be matched with WinBIZ data based on amount,
  scope, and whether they are included in the price

* The lines should be ordered by “N°” for best results

* The export encoding should be “Windows Ansi - 1252” (default)


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

* Louis Bettens <lbe@open-net.ch>
* Vincent Renaville <vincent.renaville@camptocamp.com>

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
