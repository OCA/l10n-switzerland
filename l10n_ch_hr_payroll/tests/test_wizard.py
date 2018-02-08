# -*- coding: utf-8 -*-
# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import odoo.tests.common as common

_logger = logging.getLogger(__name__)


class TestWizard(common.TransactionCase):

    def setUp(self):
        super(TestWizard, self).setUp()

        self.configs = self.env['hr.payroll.config']
        self.configs_default = self.configs.create({})

        # Test 1
        self.account_1 = self.env['account.account'].search([
            ('code', '=', '5000')], limit=1)
        self.account_2 = self.env['account.account'].search([
            ('code', '=', '2000')], limit=1)
        self.account_3 = self.env['account.account'].search([
            ('code', '=', '5800')], limit=1)
        self.account_4 = self.env['account.account'].search([
            ('code', '=', '2200')], limit=1)
        self.account_5 = self.env['account.account'].search([
            ('code', '=', '5700')], limit=1)
        self.account_6 = self.env['account.account'].search([
            ('code', '=', '2201')], limit=1)
        self.account_7 = self.env['account.account'].search([
            ('code', '=', '5700')], limit=1)
        self.account_8 = self.env['account.account'].search([
            ('code', '=', '2261')], limit=1)
        self.account_9 = self.env['account.account'].search([
            ('code', '=', '5900')], limit=1)
        self.account_10 = self.env['account.account'].search([
            ('code', '=', '5800')], limit=1)

        self.configs_test1 = self.configs.create({
            'cc': self.account_1.id,
            'basic': self.account_2.id,
            'net': self.account_3.id,
            'avs_d': self.account_4.id,
            'avs_c': self.account_5.id,
            'lpp_d': self.account_6.id,
            'lpp_c': self.account_7.id,
            'laa_c': self.account_8.id,
            'staff_ins': self.account_9.id,
            'other_costs': self.account_10.id,
            'ac_limit': 11500,
            'ac_per_off_limit': 1.2,
            'ac_per_in_limit': 2.1,
            'avs_per': 5.123,
            'pc_f_vd_per': 0.06,
            'fadmin_per': 0.23,
            'laa_per': 0.49,
            'lca_per': 0.82,
            'lpp_min': 2086.25,
            'lpp_max': 7010.00,
            'fa_amount_child': 250,
            'fa_amount_student': 330,
            'fa_min_number_childs': 3,
            'fa_amount_additional': 120
            })

        self.company = self.env.user.company_id

        # I create varius OBP contract
        self.lpp_contract = self.env['lpp.contract'].create({
            'company_id':  self.company.id,
            'name': 'DC_exemple',
            'dc_amount': 24675.00
            })
        self.lpp_contract2 = self.env['lpp.contract'].create({
            'company_id':  self.company.id,
            'name': 'DC_exemple2',
            'dc_amount': 24775.00
            })
        self.lpp_contract3 = self.env['lpp.contract'].create({
            'company_id':  self.company.id,
            'name': 'DC_exemple3',
            'dc_amount': 25675.00
            })

    def test_wizard(self):
        _logger.debug(' -- Test WIZARD -- ')

        self.assertEqual(self.configs_default.ac_limit, 12350)
        self.assertEqual(self.configs_default.ac_per_off_limit, 1.0)
        self.assertEqual(self.configs_default.ac_per_in_limit, 1.1)
        self.assertEqual(self.configs_default.avs_per, 5.125)
        self.assertEqual(self.configs_default.pc_f_vd_per, 0.06)
        self.assertEqual(self.configs_default.fadmin_per, 0)
        self.assertEqual(self.configs_default.laa_per, 0)
        self.assertEqual(self.configs_default.lca_per, 0)
        self.assertEqual(self.configs_default.lpp_min, 1762.50)
        self.assertEqual(self.configs_default.lpp_max, 7050.00)
        self.assertEqual(self.configs_default.fa_amount_child, 0)
        self.assertEqual(self.configs_default.fa_amount_student, 0)
        self.assertEqual(self.configs_default.fa_min_number_childs, 3)
        self.assertEqual(self.configs_default.fa_amount_additional, 0)
        _logger.debug('OK : Test Defaults Wizard')

        # Delete connection with the company
        self.lpp_contract2.company_id = False
        self.nb_contracts_lpp = self.env['lpp.contract'].search([])
        self.assertEqual(len(self.nb_contracts_lpp), 3)

        # I click on 'Save' button on payroll configuration
        self.configs_test1.save_configs()

        # See number of contracts before deleting
        self.nb_contracts_lpp = self.env['lpp.contract'].search([])
        self.assertEqual(len(self.nb_contracts_lpp), 2)
        _logger.debug('OK : Test if OBP contract was deleted')

        # Rules tests
        def rules_acc_equal_test(self, list_rules_types, test_code, account):
            all_equal = True
            if len(account) != 0:
                for rule_type in list_rules_types:
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
                        if res.code != test_code:
                            all_equal = False
            return all_equal

        list_rule_cc = [
            ('l10n_ch_hr_payroll.AC_E', 'credit'),
            ('l10n_ch_hr_payroll.AC_E_SOL', 'credit'),
            ('l10n_ch_hr_payroll.ALFA', 'credit'),
            ('l10n_ch_hr_payroll.AVS_E', 'credit'),
            ('l10n_ch_hr_payroll.PC_F_VD_E', 'credit'),
            ('l10n_ch_hr_payroll.BASIC_CH', 'credit'),
            ('l10n_ch_hr_payroll.LAA_E', 'credit'),
            ('l10n_ch_hr_payroll.LCA_E', 'credit'),
            ('l10n_ch_hr_payroll.LPP_E', 'credit'),
            ('l10n_ch_hr_payroll.NET_CH', 'debit')
        ]
        list_rule_basic = [
            ('l10n_ch_hr_payroll.BASIC_CH', 'debit')
        ]
        list_rule_net = [
            ('l10n_ch_hr_payroll.NET_CH', 'credit')
        ]
        list_rule_avs_d = [
            ('l10n_ch_hr_payroll.AC_C', 'debit'),
            ('l10n_ch_hr_payroll.AC_C_SOL', 'debit'),
            ('l10n_ch_hr_payroll.AC_E', 'debit'),
            ('l10n_ch_hr_payroll.AC_E_SOL', 'debit'),
            ('l10n_ch_hr_payroll.ALFA', 'debit'),
            ('l10n_ch_hr_payroll.AVS_C', 'debit'),
            ('l10n_ch_hr_payroll.AVS_E', 'debit'),
            ('l10n_ch_hr_payroll.PC_F_VD_C', 'debit'),
            ('l10n_ch_hr_payroll.PC_F_VD_E', 'debit'),
            ('l10n_ch_hr_payroll.FADMIN', 'credit')
        ]
        list_rule_avs_c = [
            ('l10n_ch_hr_payroll.AC_C', 'credit'),
            ('l10n_ch_hr_payroll.AC_C_SOL', 'credit'),
            ('l10n_ch_hr_payroll.AVS_C', 'credit'),
            ('l10n_ch_hr_payroll.PC_F_VD_C', 'credit')
        ]
        list_rule_lpp_d = [
            ('l10n_ch_hr_payroll.LPP_C', 'debit'),
            ('l10n_ch_hr_payroll.LPP_E', 'debit')
        ]
        list_rule_lpp_c = [
            ('l10n_ch_hr_payroll.LPP_C', 'credit')
        ]
        list_rule_laa_c = [
            ('l10n_ch_hr_payroll.LAA_C', 'debit'),
            ('l10n_ch_hr_payroll.LAA_E', 'debit'),
            ('l10n_ch_hr_payroll.LCA_C', 'debit'),
            ('l10n_ch_hr_payroll.LCA_E', 'debit')
        ]
        list_rule_staff_ins = [
            ('l10n_ch_hr_payroll.LAA_C', 'credit'),
            ('l10n_ch_hr_payroll.LCA_C', 'credit')
        ]
        list_rule_other_costs = [
            ('l10n_ch_hr_payroll.FADMIN', 'debit')
        ]

        # Test if all the rules from the list have the same id as given
        self.assertEqual(True, rules_acc_equal_test(
            self, list_rule_cc, '5000', self.account_1))
        self.assertEqual(True, rules_acc_equal_test(
            self, list_rule_basic, '2000', self.account_2))
        self.assertEqual(True, rules_acc_equal_test(
            self, list_rule_net, '5800', self.account_3))
        self.assertEqual(True, rules_acc_equal_test(
            self, list_rule_avs_d, '2200', self.account_4))
        self.assertEqual(True, rules_acc_equal_test(
            self, list_rule_avs_c, '5700', self.account_5))
        self.assertEqual(True, rules_acc_equal_test(
            self, list_rule_lpp_d, '2201', self.account_6))
        self.assertEqual(True, rules_acc_equal_test(
            self, list_rule_lpp_c, '5700', self.account_7))
        self.assertEqual(True, rules_acc_equal_test(
            self, list_rule_laa_c, '2261', self.account_8))
        self.assertEqual(True, rules_acc_equal_test(
            self, list_rule_staff_ins, '5900', self.account_9))
        self.assertEqual(True, rules_acc_equal_test(
            self, list_rule_other_costs, '5800', self.account_10))
        _logger.debug('OK : Test Saved Rules')

        # Tests if values are in company
        self.assertEqual(self.company.ac_limit, 11500)
        self.assertEqual(self.company.ac_per_off_limit, -1.2)
        self.assertEqual(self.company.ac_per_in_limit, -2.1)
        self.assertEqual(self.company.avs_per, -5.123)
        self.assertEqual(self.company.pc_f_vd_per, -0.06)
        self.assertEqual(self.company.fadmin_per, 0.23)
        self.assertEqual(self.company.laa_per, -0.49)
        self.assertEqual(self.company.lca_per, -0.82)
        self.assertEqual(self.company.lpp_min, 2086.25)
        self.assertEqual(self.company.lpp_max, 7010.00)
        self.assertEqual(self.company.fa_amount_child, 250)
        self.assertEqual(self.company.fa_amount_student, 330)
        self.assertEqual(self.company.fa_min_number_childs, 3)
        self.assertEqual(self.company.fa_amount_additional, 120)
        _logger.debug('OK : Test Saved Values sent to company')
