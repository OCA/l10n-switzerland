===================================
Server environment for Ebill Paynet
===================================

.. 
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! This file is generated by oca-gen-addon-readme !!
   !! changes will be overwritten.                   !!
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
   !! source digest: sha256:3b3eafc2367be61bd5e5bdb083afb236fe006636253794969365f30d4b6d5f55
   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

.. |badge1| image:: https://img.shields.io/badge/maturity-Beta-yellow.png
    :target: https://odoo-community.org/page/development-status
    :alt: Beta
.. |badge2| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3
.. |badge3| image:: https://img.shields.io/badge/github-OCA%2Fl10n--switzerland-lightgray.png?logo=github
    :target: https://github.com/OCA/l10n-switzerland/tree/14.0/server_env_ebill_paynet
    :alt: OCA/l10n-switzerland
.. |badge4| image:: https://img.shields.io/badge/weblate-Translate%20me-F47D42.png
    :target: https://translation.odoo-community.org/projects/l10n-switzerland-14-0/l10n-switzerland-14-0-server_env_ebill_paynet
    :alt: Translate me on Weblate
.. |badge5| image:: https://img.shields.io/badge/runboat-Try%20me-875A7B.png
    :target: https://runboat.odoo-community.org/builds?repo=OCA/l10n-switzerland&target_branch=14.0
    :alt: Try me on Runboat

|badge1| |badge2| |badge3| |badge4| |badge5|

This module is based on the `server_environment` module to use files for
configuration. So we can have a different configuration for each
environment (dev, test, integration, prod).  This module define the config
variables for the `ebill_paynet` module.

Exemple of the section to put in the configuration file::

    [paynet_service.name_of_the_service]
    use_test_service": True,
    client_pid": 123456789,
    service_type": b2b,
    username": username,
    password": password,

**Table of contents**

.. contents::
   :local:

Installation
============

This module depends on:

- `server_environment` which is located on `OCA/server-env`
- `ebill_paynet`

So, please be sure that those modules have been installed properly on the system

Bug Tracker
===========

Bugs are tracked on `GitHub Issues <https://github.com/OCA/l10n-switzerland/issues>`_.
In case of trouble, please check there if your issue has already been reported.
If you spotted it first, help us to smash it by providing a detailed and welcomed
`feedback <https://github.com/OCA/l10n-switzerland/issues/new?body=module:%20server_env_ebill_paynet%0Aversion:%2014.0%0A%0A**Steps%20to%20reproduce**%0A-%20...%0A%0A**Current%20behavior**%0A%0A**Expected%20behavior**>`_.

Do not contact contributors directly about support or help with technical issues.

Credits
=======

Authors
~~~~~~~

* Camptocamp

Contributors
~~~~~~~~~~~~

* Thierry Ducrest <thierry.ducrest@camptocamp.com>
* `Trobz <https://trobz.com>`_:
  * Dung Tran <dungtd@trobz.com>
  * Hai Le Nguyen <hailn@trobz.com>

Other credits
~~~~~~~~~~~~~

The migration of this module from 13.0 to 14.0 as financially supported by Camptocamp

Maintainers
~~~~~~~~~~~

This module is maintained by the OCA.

.. image:: https://odoo-community.org/logo.png
   :alt: Odoo Community Association
   :target: https://odoo-community.org

OCA, or the Odoo Community Association, is a nonprofit organization whose
mission is to support the collaborative development of Odoo features and
promote its widespread use.

This module is part of the `OCA/l10n-switzerland <https://github.com/OCA/l10n-switzerland/tree/14.0/server_env_ebill_paynet>`_ project on GitHub.

You are welcome to contribute. To learn how please visit https://odoo-community.org/page/Contribute.
