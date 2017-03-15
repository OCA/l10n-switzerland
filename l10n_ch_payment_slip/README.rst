.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

===================================
Swiss Payment slip known as ESR/BVR
===================================


This addon allows you to print the ESR/BVR report Using Qweb report.

The ESR/BVR is grenerated as an image and is availabe in a fields
of the `l10n_ch.payment_slip` Model.

This module will also allows you to import v11 files provided
by financial institute into a bank statement

This module also adds transaction_ref field on entries in order to manage
reconciliation in multi payment context (unique reference needed on
account.move.line). Many BVR can now be printed from on invoice for each
payment terms.


Configuration
=============

You can adjust the print out of ESR/BVR, which depend on each printer,
for every company in the "BVR Data" tab.

This is especialy useful when using pre-printed paper.
An option also allow you to print the ESR/BVR in background when using
white paper.

By default address format on ESR/BVR is
`%(street)s\n%(street2)s\n%(zip)s %(city)s`
This can be change by setting System parameter
`bvr.address.format`


Usage
=====

The ESR/BVR is created each time an invoice is validated.
To modify it you have to cancel it and reconfirm the invoice.

To import v11, use the wizard provided in bank statement.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/125/9.0

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/
l10n-switzerland/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback `here <https://github.com/OCA/
l10n-switzerland/issues/new?body=module:%20
l10n_ch_payment_slip%0Aversion:%20
9.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.


Credits
=======

Contributors
------------

* Nicolas Bessi <nicolas.bessi@camptocamp.com>
* Vincent Renaville <vincent.renaville@camptocamp.com>
* Yannick Vaucher <yannick.vaucher@camptocamp.com>
* Romain Deheele <romain.deheele@camptocamp.com>
* Thomas Winteler <info@win-soft.com>
* Joël Grand-Guillaume <joel.grandguillaume@camptocamp.com>
* Guewen Baconnier <guewen.baconnier@camptocamp.com>
* Alex Comba <alex.comba@agilebg.com>
* Lorenzo Battistini <lorenzo.battistini@agilebg.com>
* Paul Catinean <paulcatinean@gmail.com>
* Paulius Sladkevičius <paulius@hbee.eu>
* David Coninckx <dco@open-net.ch>

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

