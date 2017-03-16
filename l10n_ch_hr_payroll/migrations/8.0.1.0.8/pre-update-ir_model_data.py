# -*- coding: utf-8 -*-
# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
Set the existings salary rules as non-updatable
This will ensure the update of this module won't try
to remove any existing rule not directly referenced.
This is necessary because some rules may be already in use.
"""


def migrate(cr, version):
    if not version:
        return

    query = ("UPDATE ir_model_data "
             "SET noupdate=true "
             "WHERE module='l10n_ch_hr_payroll' "
             "AND model='hr.salary.rule' ")
    cr.execute(query)
