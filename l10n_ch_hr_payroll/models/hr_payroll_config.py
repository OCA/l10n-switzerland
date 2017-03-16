# -*- coding: utf-8 -*-
# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo.addons.decimal_precision as dp
from odoo import models, fields, api


class HrPayrollConfig(models.TransientModel):
    _name = 'hr.payroll.config'

    @api.model
    def _get_default_cc(self):
        all_equal = False

        all_equal = self.search_account_by_rule([
            ('l10n_ch_hr_payroll.AC_E', 'credit'),
            ('l10n_ch_hr_payroll.AC_E_SOL', 'credit'),
            ('l10n_ch_hr_payroll.ALFA', 'credit'),
            ('l10n_ch_hr_payroll.AVS_E', 'credit'),
            ('l10n_ch_hr_payroll.PC_F_VD_E', 'credit'),
            ('l10n_ch_hr_payroll.BASIC_CH', 'credit'),
            ('l10n_ch_hr_payroll.LAA_E', 'credit'),
            ('l10n_ch_hr_payroll.LCA_E', 'credit'),
            ('l10n_ch_hr_payroll.LPP_E', 'credit'),
            ('l10n_ch_hr_payroll.NET_CH', 'debit')])

        return all_equal

    @api.model
    def _get_default_basic(self):
        all_equal = False

        all_equal = self.search_account_by_rule([
            ('l10n_ch_hr_payroll.BASIC_CH', 'debit')])

        return all_equal

    @api.model
    def _get_default_net(self):
        all_equal = False
        all_equal = self.search_account_by_rule([
            ('l10n_ch_hr_payroll.NET_CH', 'credit')])

        return all_equal

    @api.model
    def _get_default_avs_d(self):
        all_equal = False

        all_equal = self.search_account_by_rule([
            ('l10n_ch_hr_payroll.AC_C', 'debit'),
            ('l10n_ch_hr_payroll.AC_C_SOL', 'debit'),
            ('l10n_ch_hr_payroll.AC_E', 'debit'),
            ('l10n_ch_hr_payroll.AC_E_SOL', 'debit'),
            ('l10n_ch_hr_payroll.ALFA', 'debit'),
            ('l10n_ch_hr_payroll.AVS_C', 'debit'),
            ('l10n_ch_hr_payroll.AVS_E', 'debit'),
            ('l10n_ch_hr_payroll.PC_F_VD_C', 'debit'),
            ('l10n_ch_hr_payroll.PC_F_VD_E', 'debit'),
            ('l10n_ch_hr_payroll.FADMIN', 'credit')])

        return all_equal

    @api.model
    def _get_default_avs_c(self):
        all_equal = False
        all_equal = self.search_account_by_rule([
            ('l10n_ch_hr_payroll.AC_C', 'credit'),
            ('l10n_ch_hr_payroll.AC_C_SOL', 'credit'),
            ('l10n_ch_hr_payroll.AVS_C', 'credit'),
            ('l10n_ch_hr_payroll.PC_F_VD_C', 'credit')])

        return all_equal

    @api.model
    def _get_default_lpp_d(self):
        all_equal = False
        all_equal = self.search_account_by_rule([
            ('l10n_ch_hr_payroll.LPP_C', 'debit'),
            ('l10n_ch_hr_payroll.LPP_E', 'debit')])

        return all_equal

    @api.model
    def _get_default_lpp_c(self):
        all_equal = False
        all_equal = self.search_account_by_rule([
            ('l10n_ch_hr_payroll.LPP_C', 'credit')])

        return all_equal

    @api.model
    def _get_default_laa_c(self):
        all_equal = False
        all_equal = self.search_account_by_rule([
            ('l10n_ch_hr_payroll.LAA_C', 'debit'),
            ('l10n_ch_hr_payroll.LAA_E', 'debit'),
            ('l10n_ch_hr_payroll.LCA_C', 'debit'),
            ('l10n_ch_hr_payroll.LCA_E', 'debit')])

        return all_equal

    @api.model
    def _get_default_staff_ins(self):
        all_equal = False
        all_equal = self.search_account_by_rule([
            ('l10n_ch_hr_payroll.LAA_C', 'credit'),
            ('l10n_ch_hr_payroll.LCA_C', 'credit')])

        return all_equal

    @api.model
    def _get_default_other_costs(self):
        all_equal = False
        all_equal = self.search_account_by_rule([
            ('l10n_ch_hr_payroll.FADMIN', 'debit')])

        return all_equal

    @api.model
    def search_account_by_rule(self, rules_types):
        res = False
        last_res = False

        for rule_type in rules_types:
            # rule_type = ('l10n_ch_hr_payroll.AC_E','credit')
            rule = rule_type[0]
            type = rule_type[1]
            rule = self.env['hr.salary.rule'].search([
                ('id', '=', self.env.ref(rule).id)
            ])
            if rule:
                rule = rule[0]
                if type == 'debit':
                    res = rule.account_debit
                else:
                    res = rule.account_credit

                if last_res != res and last_res is not False:
                    return False
                last_res = res
        return res

    def assign_account_to_rule(self, rules, account, type):
        if account.id:
            ids = []
            for rule in rules:
                ids.append(self.env.ref(rule).id)
            rules = self.env['hr.salary.rule'].search([
                ('id', 'in', ids)
            ])
            for rule in rules:
                if type == 'debit':
                    rule.account_debit = account.id
                elif type == 'credit':
                    rule.account_credit = account.id

    # configs default values
    @api.model
    def _get_default_configs(self, config):
        val = getattr(self.env.user.company_id, config)
        if val < 0:
            val = -val
        return val

    @api.model
    def _get_default_lpp_contracts(self):
        return self.env.user.company_id.lpp_contract_ids

    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.user.company_id)

    # Accounting
    # general
    cc = fields.Many2one(
        comodel_name='account.account',
        string='Counterparty account',
        default=_get_default_cc,
        required=False)

    basic = fields.Many2one(
        comodel_name='account.account',
        string='Gross Salary',
        default=_get_default_basic,
        required=False)

    net = fields.Many2one(
        comodel_name='account.account',
        string='Net Salary',
        default=_get_default_net,
        required=False)

    # standard
    avs_d = fields.Many2one(
        comodel_name='account.account',
        string='Social Insurance (OAI/II/IC)',
        default=_get_default_avs_d,
        required=False)

    avs_c = fields.Many2one(
        comodel_name='account.account',
        string='Social charges (OAI/II/IC)',
        default=_get_default_avs_c,
        required=False)

    lpp_d = fields.Many2one(
        comodel_name='account.account',
        string='Institutions of Providence (OBP)',
        default=_get_default_lpp_d,
        required=False)

    lpp_c = fields.Many2one(
        comodel_name='account.account',
        string='Social charges (OBP)',
        default=_get_default_lpp_c,
        required=False)

    laa_c = fields.Many2one(
        comodel_name='account.account',
        string='Debts AI',
        default=_get_default_laa_c,
        required=False)

    # special
    staff_ins = fields.Many2one(
        comodel_name='account.account',
        string='Staff Insurance',
        default=_get_default_staff_ins,
        required=False)

    other_costs = fields.Many2one(
        comodel_name='account.account',
        string='Other staff costs',
        default=_get_default_other_costs,
        required=False)

    # Parameters
    # UI(AC)
    ac_limit = fields.Float(
        string='Maximum limit',
        default=lambda self: self._get_default_configs('ac_limit'),
        digits=dp.get_precision('Account'),
        required=False)
    ac_per_off_limit = fields.Float(
        string='Percentage (off limit) (%)',
        default=lambda self: self._get_default_configs('ac_per_off_limit'),
        digits=dp.get_precision('Payroll Rate'),
        required=False)
    ac_per_in_limit = fields.Float(
        string='Percentage (%)',
        default=lambda self: self._get_default_configs('ac_per_in_limit'),
        digits=dp.get_precision('Payroll Rate'),
        required=False)

    # OAI(AVS)
    avs_per = fields.Float(
        string='Percentage (%)',
        default=lambda self: self._get_default_configs('avs_per'),
        digits=dp.get_precision('Payroll Rate'),
        required=False)

    # FADMIN
    fadmin_per = fields.Float(
        string="Percentage (%)",
        default=lambda self: self._get_default_configs('fadmin_per'),
        digits=dp.get_precision('Payroll Rate'),
        required=False)

    # AI(LAA)
    laa_per = fields.Float(
        string="Percentage (%)",
        default=lambda self: self._get_default_configs('laa_per'),
        digits=dp.get_precision('Payroll Rate'),
        required=False)

    # SDA(LCA)
    lca_per = fields.Float(
        string="Percentage (%)",
        default=lambda self: self._get_default_configs('lca_per'),
        digits=dp.get_precision('Payroll Rate'),
        required=False)

    # AS Families (PC Familles)
    pc_f_vd_per = fields.Float(
        string="Percentage (%)",
        default=lambda self: self._get_default_configs('pc_f_vd_per'),
        digits=dp.get_precision('Payroll Rate'),
        required=False)

    # OBP(LPP)
    lpp_min = fields.Float(
        string="Minimum legal",
        default=lambda self: self._get_default_configs('lpp_min'),
        digits=dp.get_precision('Account'),
        required=False)
    lpp_max = fields.Float(
        string="Maximum legal",
        default=lambda self: self._get_default_configs('lpp_max'),
        digits=dp.get_precision('Account'),
        required=False)

    # Family allowances
    fa_amount_child = fields.Float(
        string="Amount per child (0-16)",
        default=lambda self: self._get_default_configs('fa_amount_child'),
        digits=dp.get_precision('Account'),
        required=False)
    fa_amount_student = fields.Float(
        string="Amount per student (16+)",
        default=lambda self: self._get_default_configs('fa_amount_student'),
        digits=dp.get_precision('Account'),
        required=False)
    fa_min_number_childs = fields.Integer(
        string="Additional allowance for the",
        default=lambda self: self._get_default_configs('fa_min_number_childs'),
        required=False)
    fa_amount_additional = fields.Float(
        string="Additional allowance amount",
        default=lambda self: self._get_default_configs('fa_amount_additional'),
        digits=dp.get_precision('Account'),
        required=False)

    lpp_contract_ids = fields.One2many(
        string="OBP contract ids",
        related="company_id.lpp_contract_ids",
        default=lambda self: self._get_default_lpp_contracts(),
        ondelete='cascade')

    def values_to_company(self):
        company_id = self.company_id
        list_fields = [
            'ac_limit',
            'fadmin_per',
            'lpp_min',
            'lpp_max',
            'fa_amount_child',
            'fa_amount_student',
            'fa_min_number_childs',
            'fa_amount_additional'
        ]
        list_fields_neg = [
            'ac_per_off_limit',
            'ac_per_in_limit',
            'avs_per',
            'laa_per',
            'lca_per',
            'pc_f_vd_per'
        ]

        for value in list_fields:
            value_field = getattr(self, value)
            company_id.write({value: value_field})

        for value in list_fields_neg:
            value_field = -(getattr(self, value))
            company_id.write({value: value_field})

    def delete_lpp_contracts(self):
        ids_to_unlink = self.env['lpp.contract'].search([
            ('company_id', '=', False)
        ])
        ids_to_unlink.unlink()

    # save and create configs
    @api.multi
    def save_configs(self):
        for config in self:
            # -Save codes-
            # cc
            config.assign_account_to_rule([
                'l10n_ch_hr_payroll.AC_E',
                'l10n_ch_hr_payroll.AC_E_SOL',
                'l10n_ch_hr_payroll.ALFA',
                'l10n_ch_hr_payroll.AVS_E',
                'l10n_ch_hr_payroll.PC_F_VD_E',
                'l10n_ch_hr_payroll.BASIC_CH',
                'l10n_ch_hr_payroll.LAA_E',
                'l10n_ch_hr_payroll.LCA_E',
                'l10n_ch_hr_payroll.LPP_E'
                ], config.cc, 'credit')
            config.assign_account_to_rule([
                'l10n_ch_hr_payroll.NET_CH'
                ], config.cc, 'debit')

            # basic
            config.assign_account_to_rule([
                'l10n_ch_hr_payroll.BASIC_CH'
                ], config.basic, 'debit')

            # net
            config.assign_account_to_rule([
                'l10n_ch_hr_payroll.NET_CH'
                ], config.net, 'credit')

            # avs_d
            config.assign_account_to_rule([
                'l10n_ch_hr_payroll.AC_C',
                'l10n_ch_hr_payroll.AC_C_SOL',
                'l10n_ch_hr_payroll.AC_E',
                'l10n_ch_hr_payroll.AC_E_SOL',
                'l10n_ch_hr_payroll.ALFA',
                'l10n_ch_hr_payroll.AVS_C',
                'l10n_ch_hr_payroll.AVS_E',
                'l10n_ch_hr_payroll.PC_F_VD_C',
                'l10n_ch_hr_payroll.PC_F_VD_E'
                ], config.avs_d, 'debit')
            config.assign_account_to_rule([
                'l10n_ch_hr_payroll.FADMIN'
                ], config.avs_d, 'credit')

            # avs_c
            config.assign_account_to_rule([
                'l10n_ch_hr_payroll.AC_C',
                'l10n_ch_hr_payroll.AC_C_SOL',
                'l10n_ch_hr_payroll.AVS_C',
                'l10n_ch_hr_payroll.PC_F_VD_C'
                ], config.avs_c, 'credit')

            # lpp_d
            config.assign_account_to_rule([
                'l10n_ch_hr_payroll.LPP_C',
                'l10n_ch_hr_payroll.LPP_E'
                ], config.lpp_d, 'debit')

            # lpp_c
            config.assign_account_to_rule([
                'l10n_ch_hr_payroll.LPP_C'
                ], config.lpp_c, 'credit')

            # laa_c
            config.assign_account_to_rule([
                'l10n_ch_hr_payroll.LAA_C',
                'l10n_ch_hr_payroll.LAA_E',
                'l10n_ch_hr_payroll.LCA_C',
                'l10n_ch_hr_payroll.LCA_E'
                ], config.laa_c, 'debit')

            # staff_ins
            config.assign_account_to_rule([
                'l10n_ch_hr_payroll.LAA_C',
                'l10n_ch_hr_payroll.LCA_C'
                ], config.staff_ins, 'credit')

            # other_costs
            config.assign_account_to_rule([
                'l10n_ch_hr_payroll.FADMIN'
                ], config.other_costs, 'debit')

            # -Save values in company
            config.values_to_company()

            # Search lpp contracts without company id
            config.delete_lpp_contracts()

        return True
