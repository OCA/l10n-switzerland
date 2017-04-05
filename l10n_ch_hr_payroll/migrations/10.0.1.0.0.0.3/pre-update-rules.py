# -*- coding: utf-8 -*-
#
#  File: /pre-update-rules.py
#  Module: l10n_ch_hr_payroll
#
#  Created by lfr@open-net.ch
#
#  Copyright (c) 2017-TODAY Open-Net Ltd.
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

"""
Set the existings salary rules as non-updatable
This will ensure the update of this module won't try
to remove any existing rule not directly referenced.
This is necessary because some rules may be already in use.
"""

import logging
#Get the logger
_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    migrate_category(cr, 'hr_payroll_P13', 'ALW')
    migrate_category(cr, 'hr_payroll_HSUP', 'DED')
    migrate_category(cr, 'hr_payroll_BONUS', 'DED')

def migrate_category(cr, old_cat, new_cat):
    query = ("SELECT res_id FROM ir_model_data "
             "WHERE module='l10n_ch_hr_payroll' and name = '%s' " % old_cat)
    cr.execute(query)
    old_cat_id = cr.fetchall()

    if old_cat_id:
        old_cat_id = old_cat_id[0][0]

        # Update the references of the old category
        # to a new one
        query = ("SELECT res_id FROM ir_model_data "
                "WHERE module='hr_payroll' and name = '%s' " % new_cat)
        cr.execute(query)
        new_cat_id = cr.fetchall()
        new_cat_id = new_cat_id[0][0]

        query = ("UPDATE hr_salary_rule "
                "SET category_id=%s "
                "WHERE category_id=%s" % (new_cat_id, old_cat_id))
        cr.execute(query)

        query = ("UPDATE hr_payslip_line "
                "SET category_id=%s "
                "WHERE category_id=%s" % (new_cat_id, old_cat_id))
        cr.execute(query)

        # Delete the old category
        query = ("DELETE FROM ir_model_data "
            "WHERE res_id=%s" % old_cat_id)
        cr.execute(query)
        query = ("DELETE FROM hr_salary_rule_category "
                "WHERE id=%s" % old_cat_id)
        cr.execute(query)

