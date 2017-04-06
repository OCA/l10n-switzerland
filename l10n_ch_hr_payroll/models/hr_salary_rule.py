# -*- coding: utf-8 -*-
# © 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api
from odoo.tools.safe_eval import safe_eval


class HrSalaryRule(models.Model):

    _inherit = 'hr.salary.rule'
    name = fields.Char(translate=True)
    note = fields.Char(translate=True)

    percentage = fields.Float(
        compute="_compute_percentage_from_company",
        required=False)
    amount_base = fields.Float(
        required=False)

    @api.multi
    def _compute_percentage_from_company(self):
        list_fields_per = {
            'fadmin_per': ['l10n_ch_hr_payroll.FADMIN'],
            'avs_per': ['l10n_ch_hr_payroll.AVS_C',
                        'l10n_ch_hr_payroll.AVS_E'],
            'laa_per': ['l10n_ch_hr_payroll.LAA_C',
                        'l10n_ch_hr_payroll.LAA_E'],
            'lca_per': ['l10n_ch_hr_payroll.LCA_C',
                        'l10n_ch_hr_payroll.LCA_E'],
            'ac_per_off_limit': ['l10n_ch_hr_payroll.AC_C_SOL',
                                 'l10n_ch_hr_payroll.AC_E_SOL'],
            'ac_per_in_limit': ['l10n_ch_hr_payroll.AC_C',
                                'l10n_ch_hr_payroll.AC_E']
        }

        for rule in self:
            for rule_from, rules_to in list_fields_per.items():
                for rule_to in rules_to:
                    rule_to_modify = rule.env['hr.salary.rule'].search([
                        ('id', '=', rule.env.ref(rule_to).id)
                    ])

                    if rule_to_modify.id == rule.id:
                        rule.percentage = getattr(rule.company_id, rule_from)

    @api.multi
    def compute_rule(self, localdict):
        res = super(HrSalaryRule, self).compute_rule(localdict)

        for rule in self:
            if rule.amount_percentage_base:
                rule.amount_base = \
                    float(safe_eval(rule.amount_percentage_base, localdict))
            if rule.id == self.env.ref("l10n_ch_hr_payroll.LPP_C").id or \
                    rule.id == self.env.ref("l10n_ch_hr_payroll.LPP_E").id:
                rule.percentage = \
                    -float(safe_eval("contract.lpp_rate or 100", localdict))

            if rule.id == self.env.ref("l10n_ch_hr_payroll.IMP_SRC").id:
                rule.percentage = \
                    -float(safe_eval("contract.imp_src or 100", localdict))
        return res
