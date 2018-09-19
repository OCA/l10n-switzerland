[ This file must be max 2-3 paragraphs, and is required. ]

Switzerland Payroll Rules
=========================

This module allows you to manage the salaries of your employees

** Features list :**
    * Add Swiss salary rule categories
    * Add Swiss salary rules
    * Add children in school to employee
    * Add LPP range to contract
    * Add LPP Amount to contract.
    * Add Holiday Rate to contract.

** For further information:**
    * Payroll accounting: http://open-net.ch/blog/la-comptabilite-salariale-suisse-avec-odoo-1/tag/salaires-6

** Remarks: **
    * To prevent overwriting your salary rules changes, an update from 1.0.8 and lower to 1.0.9 and higher creates duplicates of the salary rules. This is because with some migrated databases, one may encounter a difficulty with the existing rules (they can not be erased if they are already used). The solution is then to force the existing ones to be non-updatable. And this is done using an included pre-migration script.
    * As this module proposes its own report (same as the original, but with its own footer), don't forget to make it non-updatable.
    * If you choose to uninstall this module, you have to manually delete the rules.
