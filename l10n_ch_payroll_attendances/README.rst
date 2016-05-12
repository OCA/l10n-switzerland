.. image:: https://img.shields.io/badge/licence-AGPL--3-blue.svg
    :alt: License: AGPL-3

Attendances and timesheet improvements
======================================

This module allows you to add commission and reimbursement to payslip

**Features list :**
    * Add an hourly rate as a base for salary compensation computing
    * Add a link payslip to hr_holiday
    * Compute payslip attendances based on employe's schedule and employe's attendance

Installation
============
To install this module, you need to:
#. Go to Applications, search for the module and install by pressing the button.

Configuration
=============

There is no configuration required to use this module.

Usage
=====
- To start using this module, you need to configure a contract on your employees.
- This contract must contain a Working Schedule.

**For exemple :**
    .. image:: http://s23.postimg.org/hkzqbz83f/Screen_Shot_04_13_16_at_02_38_PM.png

- Here you can see in red the fields added by the module.
- These fields are used in employee's payslip to determin time and wage compensation.
- Once you've configured the working schedule for each employee.
- You can create payslip for your employees.

**For exemple :**
    .. image:: http://s23.postimg.org/cghcwp5mj/Screen_Shot_04_13_16_at_02_58_PM.png

- Here you can see in red two new elements : 
    - A new button to compute the attendances
    - A new tab to see the result of the computation
- Into the result of the computation tab you can see something like this :

.. image:: http://s28.postimg.org/bittrg17h/Screen_Shot_04_13_16_at_03_05_PM.png

- This result is used to create allocation request if time compensation was set.
- It is also used to add salary compensation if you correctly set the corresponding rule into the salary structur of the employee.

Known issues / Roadmap
======================

* ...

Bug Tracker
===========

Bugs are tracked on `GitHub Issues
<https://github.com/OCA/{project_repo}/issues>`_. In case of trouble, please
check there if your issue has already been reported. If you spotted it first,
help us smashing it by providing a detailed and welcomed feedback.

Credits
=======

Images
------

* Odoo Community Association: `Icon <https://github.com/OCA/maintainer-tools/blob/master/template/module/static/description/icon.svg>`_.

Contributors
------------

* David Coninckx <dco@open-net.ch>

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