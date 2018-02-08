# -*- coding: utf-8 -*-
# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import odoo.tests.common as common
from datetime import datetime, timedelta
from odoo.fields import Date

_logger = logging.getLogger(__name__)


class TestContractLPP(common.TransactionCase):

    def setUp(self):
        super(TestContractLPP, self).setUp()

        # Some salary rules references
        self.basic_ch = self.ref('l10n_ch_hr_payroll.BASIC_CH')
        self.gross_ch = self.ref('l10n_ch_hr_payroll.GROSS_CH')
        self.net_ch = self.ref('l10n_ch_hr_payroll.NET_CH')
        self.ac_c = self.ref('l10n_ch_hr_payroll.AC_C')
        self.ac_c_sol = self.ref('l10n_ch_hr_payroll.AC_C_SOL')
        self.ac_e = self.ref('l10n_ch_hr_payroll.AC_E')
        self.ac_e_sol = self.ref('l10n_ch_hr_payroll.AC_E_SOL')
        self.alfa = self.ref('l10n_ch_hr_payroll.ALFA')
        self.avs_c = self.ref('l10n_ch_hr_payroll.AVS_C')
        self.avs_e = self.ref('l10n_ch_hr_payroll.AVS_E')
        self.pc_f_vd_c = self.ref('l10n_ch_hr_payroll.PC_F_VD_C')
        self.pc_f_vd_e = self.ref('l10n_ch_hr_payroll.PC_F_VD_E')
        self.laa_c = self.ref('l10n_ch_hr_payroll.LAA_C')
        self.laa_e = self.ref('l10n_ch_hr_payroll.LAA_E')
        self.lca_c = self.ref('l10n_ch_hr_payroll.LCA_C')
        self.lca_e = self.ref('l10n_ch_hr_payroll.LCA_E')
        self.lpp_c = self.ref('l10n_ch_hr_payroll.LPP_C')
        self.lpp_e = self.ref('l10n_ch_hr_payroll.LPP_E')
        self.imp_src = self.ref('l10n_ch_hr_payroll.IMP_SRC')

        # I create a new employee "Richard"
        self.richard_emp = self.env['hr.employee'].create({
            'name': 'Richard',
            'children': 2,
            'children_student': 1
        })

        # List of rules needed
        self.rules_for_structure = [
            self.basic_ch,
            self.gross_ch,
            self.net_ch,
            self.ac_c,
            self.ac_e,
            self.ac_c_sol,
            self.ac_e_sol,
            self.alfa,
            self.avs_c,
            self.avs_e,
            self.pc_f_vd_c,
            self.pc_f_vd_e,
            self.laa_c,
            self.laa_e,
            self.lca_c,
            self.lca_e,
            self.lpp_c,
            self.lpp_e,
            self.imp_src
            ]

        # I create a salary structure for "Software Developer"
        self.developer_pay_structure = self.env['hr.payroll.structure'].create(
            {
                'name': 'Salary Structure for Software Developer',
                'code': 'SD',
                'company_id': self.ref('base.main_company'),
                'rule_ids': [(6, 0, self.rules_for_structure)],
                'parent_id': 0
            })

        # I create a OBP contract
        self.lpp_contract = self.env['lpp.contract'].create({
            'company_id':  self.ref('base.main_company'),
            'name': 'DC_exemple',
            'dc_amount': 24675.00
            })

        # I create a contract for "Richard"
        self.richard_contract = self.env['hr.contract'].create({
            'date_end': Date.to_string((datetime.now() + timedelta(days=365))),
            'date_start': Date.today(),
            'name': 'Contract for Richard',
            'wage_fulltime': 7500.0,
            'occupation_rate': 20.0,
            'wage': 0,
            'wage_type': 'month',
            'imp_src': 0,
            'lpp_contract_id': self.lpp_contract.id,
            'lpp_rate': 8.650,
            'lpp_amount': 0,
            'type_id': self.ref('hr_contract.hr_contract_type_emp'),
            'employee_id': self.richard_emp.id,
            'struct_id': self.developer_pay_structure.id
            })

        # I create a payslip for "Richard"
        self.richard_payslip = self.env['hr.payslip'].create({
            'name': 'Payslip of Richard',
            'employee_id': self.richard_emp.id,
            'company_id': self.ref('base.main_company'),
            'contract_id': self.richard_contract.id,
            'working_days': 26,
            'non_working_days': 12
            })

        # I create payroll config with company values
        self.configs = self.env['hr.payroll.config'].create({
            'ac_limit': 12350,
            'ac_per_off_limit': 1.0,
            'ac_per_in_limit': 1.1,
            'avs_per': 5.125,
            'pc_f_vd_per': 0.06,
            'fadmin_per': 0.25,
            'laa_per': 0.46,
            'lca_per': 0.52,
            'lpp_min': 1762.50,
            'lpp_max': 7050.00,
            'fa_amount_child': 250,
            'fa_amount_student': 330,
            'fa_min_number_childs': 3,
            'fa_amount_additional': 120
            })

    def test_contract_lpp(self):
        _logger.debug(' -- Test CONTRACT -- ')
        _logger.debug(self.configs.avs_per)

        # I click on 'Save' button on payroll configuration
        self.configs.save_configs()

        # OnChange wage full-time and occupation rate to calcule wage
        self.richard_contract._onchange_wage_rate_fulltime()
        self.assertEqual(self.richard_contract.wage, 1500)

        # OnChange working days and non working days to calcule working rate
        self.richard_payslip._onchange_working_non_working_days()
        self.assertEqual(self.richard_payslip.working_rate, (26-12)/26.0*100)

        # I click on 'Compute Sheet' button on payslip
        self.richard_payslip.compute_sheet()

        rule_lines = self.richard_payslip.line_ids.search([
            ('salary_rule_id', 'in', self.rules_for_structure)
        ])

        _logger.debug('Test w/ contract LPP')

        for line in rule_lines:
            # BASIC CH
            if line.salary_rule_id.id == self.basic_ch:
                self.assertEqual(
                    line.python_amount,
                    round((1500*((26-12)/26.0)), 2))
                _logger.debug('BASIC CH %s' % line.python_amount)

            # GROSS CH
            if line.salary_rule_id.id == self.gross_ch:
                self.assertEqual(
                    line.python_amount,
                    round((1500*((26-12)/26.0)+950), 2))

            # NET CH
            if line.salary_rule_id.id == self.net_ch:
                self.assertEqual(
                    line.python_amount,
                    round(1648.30, 2))

            # UI (AC)
            if line.salary_rule_id.id == self.ac_c:
                self.assertEqual(
                    line.python_amount,
                    round((1500*((26-12)/26.0)), 2))
                self.assertEqual(line.python_rate, -1.1)
                self.assertEqual(line.total, -8.88)
            if line.salary_rule_id.id == self.ac_e:
                self.assertEqual(
                    line.python_amount,
                    round((1500*((26-12)/26.0)), 2))
                self.assertEqual(line.python_rate, -1.1)
                self.assertEqual(line.total, -8.88)
            # UI (AC) - SOL
            if line.salary_rule_id.id == self.ac_c_sol:
                self.assertEqual(
                    line.python_amount, 0)
                self.assertEqual(line.python_rate, -1.1)
                self.assertEqual(line.total, 0)
            if line.salary_rule_id.id == self.ac_e_sol:
                self.assertEqual(
                    line.python_amount, 0)
                self.assertEqual(line.python_rate, -1.1)
                self.assertEqual(line.total, 0)

            # ALFA
            if line.salary_rule_id.id == self.alfa:
                self.assertEqual(
                    line.python_amount,
                    round((2*250)+330+120, 2))
                self.assertEqual(line.python_rate, 100)
                self.assertEqual(line.total, 950)

            # OAI (AVS)
            if line.salary_rule_id.id == self.avs_c:
                self.assertEqual(
                    line.python_amount,
                    round((1500*((26-12)/26.0)), 2))
                self.assertEqual(line.python_rate, -5.125)
                self.assertEqual(line.total, -41.39)
            if line.salary_rule_id.id == self.avs_e:
                self.assertEqual(
                    line.python_amount,
                    round((1500*((26-12)/26.0)), 2))
                self.assertEqual(line.python_rate, -5.125)
                self.assertEqual(line.total, -41.39)

            # AS Families (PC Famille)
            if line.salary_rule_id.id == self.pc_f_vd_c:
                self.assertEqual(
                    line.python_amount,
                    round((1500*((26-12)/26.0)), 2))
                self.assertEqual(line.python_rate, -0.06)
                self.assertEqual(line.total, -0.48)
            if line.salary_rule_id.id == self.pc_f_vd_e:
                self.assertEqual(
                    line.python_amount,
                    round((1500*((26-12)/26.0)), 2))
                self.assertEqual(line.python_rate, -0.06)
                self.assertEqual(line.total, -0.48)

            # IMP_SRC
            if line.salary_rule_id.id == self.imp_src:
                self.assertEqual(line.python_amount, 0)
                self.assertEqual(line.python_rate, 0)
                self.assertEqual(line.total, 0)

            # AI (LAA)
            if line.salary_rule_id.id == self.laa_c:
                self.assertEqual(
                    line.python_amount,
                    round((1500*((26-12)/26.0)), 2))
                self.assertEqual(line.python_rate, -0.46)
                self.assertEqual(line.total, -3.72)
            if line.salary_rule_id.id == self.laa_e:
                self.assertEqual(
                    line.python_amount,
                    round((1500*((26-12)/26.0)), 2))
                self.assertEqual(line.python_rate, -0.46)
                self.assertEqual(line.total, -3.72)

            # SDA (LCA)
            if line.salary_rule_id.id == self.lca_c:
                self.assertEqual(
                    line.python_amount,
                    round((1500*((26-12)/26.0)), 2))
                self.assertEqual(line.python_rate, -0.52)
                self.assertEqual(line.total, -4.20)
            if line.salary_rule_id.id == self.lca_e:
                self.assertEqual(
                    line.python_amount,
                    round((1500*((26-12)/26.0)), 2))
                self.assertEqual(line.python_rate, -0.52)
                self.assertEqual(line.total, -4.20)

            # OBP (LPP)
            if line.salary_rule_id.id == self.lpp_c:
                calc_lpp = (((7500.0*12) - 24675)/12)*(20.0/100)*((26-12)/26.0)
                self.assertEqual(
                    line.python_amount,
                    round(calc_lpp, 2))
                self.assertEqual(line.python_rate, -8.650)
                self.assertEqual(line.total, -50.71)
            if line.salary_rule_id.id == self.lpp_e:
                calc_lpp = (((7500.0*12) - 24675)/12)*(20.0/100)*((26-12)/26.0)
                self.assertEqual(
                    line.python_amount,
                    round(calc_lpp, 2))
                self.assertEqual(line.python_rate, -8.650)
                self.assertEqual(line.total, -50.71)
