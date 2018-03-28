.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

LSV and Postfinance Direct Debit file generator
===============================================

Features:
---------
    * LSV file generation
    * Postfinance Direct Debit file generation
    * Invoice freeing. You can "free" an invoice that is in a direct debit \
      order. This is because you have sometimes to generate 2 direct debit \
      order for the same invoice (i.e. if debit fails the first time).

Installation
============

To install this module, you need to have the module account_banking_sepa_direct_debit found in OCA/bank-payment
repository.

Configuration
=============

For LSV file generation, don't forget :
    * To set your LSV identifier in your beneficiary bank account.
    * To set your BVR identifier in your beneficiary bank account if you want \
      to use BVR references.
    * To setup a payment mode with payment type "LSV Direct Debit"
    * That each partner which is concerned by LSV has to have a valid bank \
      account with a valid mandate..

For postfinance DD file generation, don't forget :
    * To set your Postfinance DD identifier in your beneficiary BVR account.
    * To setup a payment mode with payment type "Postfinance Direct Debit"
    * That each partner which is concerned by Postfinance DD has to have a \
      valid BV account with a valid mandate.

Usage
=====

    * Create some invoices for partners with well configured bank accounts.
    * Create a Direct Debit order with a payment mode having LSV/DD payment \
      type.
    * Make sure that due dates are in the valid range if you chose "Due date" \
      as preferred execution date.
    * Press "Confirm payments"
    * Press "Make payments". This will launch the LSV/DD file generation \
      wizard.
    * Download the generated file and press "Validate". If you need to \
      download the file again, you can access the generated file with the \
      "Generated Direct Debit Files" menu.

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/125/8.0

For further information, please visit:

* https://www.odoo.com/forum/help-1

Known issues / Roadmap
======================

Currently, only BVR reference usage is implemented (using l10n_ch_payment_slip
 module) for LSV refernece. IPI usage is not implemented yet, this way an
 error occurs if no BVR ref are set in invoices.

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-switzerland/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us smashing it by providing a detailed and welcomed feedback.


Credits
=======

Contributors
------------

* Cyril Sester <cyril.sester@outlook.com>
* Steve Ferry <steve.ferry1992@gmail.com>
* Carlos Serra-Toro <carlos.serra@braintec-group.com>

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