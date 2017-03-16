# -*- coding: utf-8 -*-
# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

"""
This sets a new category to the rules and payslip lines that
use old categories that are not used anymore and then delete
those old categories
"""


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
                 "WHERE module='l10n_ch_hr_payroll' "
                 "and name = '%s' and res_id=%s" % (old_cat, old_cat_id))
        cr.execute(query)
        query = ("DELETE FROM hr_salary_rule_category "
                 "WHERE id=%s" % old_cat_id)
        cr.execute(query)
