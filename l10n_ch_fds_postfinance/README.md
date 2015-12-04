.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
   :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
   :alt: License: AGPL-3

==================================
Postfinance File Delivery Services
==================================

The file delivery services (FDS) is a service offered by Postfinance AG Technology unit service.

FDS acts as a gateway between external networks and the Post CH SA. It enables mutual exchange of files between partners and Post CH applications.

This module allows Odoo users to import files from their FDS PostFinance and convert imported files to bank statment.

Features
--------
* Manage FDS Account users
* Generate authentication key pairs for new FDS users
* Import existing authentication key pairs for FDS
* Download files from FDS PostFinance SFTP and import them to Bank Statements

additional addons:       
------------------
* upload PostFinance Direct Debit generate file to FDS PostFinance
* upload SEPA generate file to FDS PostFinance

Installation
============

In order to be able to use the module, you need to have a Postfinance FDS
Account. You can generate authentication key pairs for your users (to allow
them using the service) from the module.

To generate a new private key in the database, you need to launch odoo with
the option --ssh_pwd=your_password or add it to your config file:
ssh_pwd = your_password

external dependencies:
----------------------
* python module: pysftp
* python module: pycrypto

Configuration
=============

To configure this module, you need to:

* Setup your FDS Postfinance Account
  (menu: Accounting/Configuration/Accounts/FDS Postfinance Account)

    * hostname: the hostname of FDS Postfinance (fds.post.ch)
    * username: username for SFTP given by Postfinance
    * postfinance_email: the public key must be sent to this mail (fds@post.ch)
    * user_id: the public key must be sent by the contact person of the company concerned (or appear in the exchange of mail)
* Import or generate new authentication keys for each user that should have access to FDS files
* Verify the SFTP connection
* Configure directories access rights

Usage
=====

To import files as bank statement:

* Go to Accounting/Bank and Cash/FDS PostFinance files
* Select an Account
* Click on More to download files from the SFTP server
* In case of error, the file is kept and you can import it manually

.. image:: https://odoo-community.org/website/image/ir.attachment/5784_f2813bd/datas
   :alt: Try me on Runbot
   :target: https://runbot.odoo-community.org/runbot/125/8.0

.. repo_id is available in https://github.com/OCA/maintainer-tools/blob/master/tools/repos_with_ids.txt
.. branch is "8.0" for example

Known issues / Roadmap
======================

* [not implemented yet] send authentication key to FDS Postfiance by e-mail
  (for now, download public key and send the email to postfinance manually)
* [not implemented yet] CRON job to automatically import download files from FDS PostFinance SFTP to Bank Statement

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/l10n-switzerland/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed `feedback
<https://github.com/OCA/
l10n-switzerland/issues/new?body=module:%20
l10n_ch_fds_postfinance%0Aversion:%20
8.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* Nicolas Tran <nox.tran@gmail.com>
* Emanuel Cino <ecino@compassion.ch>

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
