.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Postfinance File Delivery Services
==================================
The file delivery services (FDS) is service offered by Postfinance AG Technology unit service.

FDS acts as a gateway between external networks and the Post CH SA. It enables mutual exchange of files between partners and Post CH applications.

Benefit
-------
This module allow Odoo users to import files on their FDS PostFinance and convert imported files to bank statment.

Features
--------
* list and import download files from FDS PostFinance SFTP to Bank Statement
* generate authentication key for FDS Postfinance SFTP 
* import authentication key for FDS Postfianance SFTP
* [not implemented yet] send authentication key to FDS Postfiance mail 
  (for now, download public key and send the email to postfinance manually)
* [not implemented yet] timer to automatically import download files from FDS PostFinance SFTP to Bank Statement

Installation
------------
To install this module, you need to add the fds postfinance module into your addons path.

To encrypte new private key in the database, you need to add to your odoo config (odoo.conf): ssh_pwd = your_password 

Configuration
-------------
* Setup FDS Postfinance (path: Accounting/Configuration/Accounts/FDS Postfinance Account)

    * hostname: the hostname of FDS Postfinance (fds.post.ch)
    * user_id: user id given by Postfinance
    * mail: the public key must be sent to this mail (fds@post.ch)
    * company_contact: the public key must be sent by the contact person of the company concerned (or appear in the exchange of mail)
* import or generate a new authentication key (on FDS authentication key)
* verify the SFTP connection (on Configuration FDS directory)
* select which directory allow to download or upload files

Usage
-----
* to import files as bank statement, use the more button.
* in case of error, the file is kept and you can import manually 

Security user access
--------------------
* to the import : Accounting & Finance -> Accountant
* to the FDS configuration account (R): Accounting & Finance -> Financial Manager
* to the FDS configuration account (W): Administration -> Settings

dependency:
-----------
* account_accountant module
* l10n_ch_account_statement_base_import module

external dependency:
--------------------
* python module: pysftp
* python module: pycrypto 

additional addons:       
------------------
* upload PostFinance Direct Debit generate file to FDS PostFinance 
* upload SEPA generate file to FDS PostFinance 

Credits
=======

Contributors
------------

* Nicolas Tran <nox.tran@gmail.com>
* Please Compassion put your email here.

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