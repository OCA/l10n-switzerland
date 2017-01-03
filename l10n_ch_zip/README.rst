.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3


============================
Swiss postal code (ZIP) list
============================

This module will load all the Swiss postal codes (ZIP) to ease the input
of partners.

It is not mandatory to use them in Odoo in Switzerland, but can improve
the user experience.


Installation
============

To install this module, you need to:

* download and install manually
* or directly install it over Odoo-Apps


Dependencies
============

The module ``base_location`` is required. It is available in
https://github.com/OCA/partner-contact/

Since Version 8.0.2.0 the module ``l10n_ch_states`` is required.
It is also available in https://github.com/OCA/l10n-switzerland


Configuration
=============

To configure this module, you need to:

* do nothing


Usage
=====

To use this module, you need to:

* Fill the new field in the partner form with a zip or a city from Switzerland
* Than you get a list with possible entries.
* The one you select is auto-filled in the zip-, citiy-, state- and country-field.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/125/10.0

Known issues / Roadmap
======================

* actually there are no issues known


Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-switzerland/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback.


Credits
=======

Contributors
------------

* Nicolas Bessi (Camptocamp)
* Olivier Jossen (Brain Tec)
* Guewen Baconnier (Camptocamp)
* Mathias Neef (copadoMEDIA)
* Yannick Vaucher (Camptocamp)

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
