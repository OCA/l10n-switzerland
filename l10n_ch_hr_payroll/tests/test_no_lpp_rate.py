# -*- coding: utf-8 -*-
# Copyright 2017 Open Net Sàrl
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import odoo.tests.common as common
from datetime import datetime, timedelta
from odoo.fields import Date

_logger = logging.getLogger(__name__)


class TestNoLPP(common.TransactionCase):

    def setUp(self):
        super(TestNoLPP, self).setUp()

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

        # I create a contract for "Richard"
        self.richard_contract = self.env['hr.contract'].create({
            'date_end': Date.to_string((datetime.now() + timedelta(days=365))),
            'date_start': Date.today(),
            'name': 'Contract for Richard',
            'wage': 50,
            'imp_src': 0,
            'lpp_rate': 0,
            'lpp_amount': 200,
            'type_id': self.ref('hr_contract.hr_contract_type_emp'),
            'employee_id': self.richard_emp.id,
            'struct_id': self.developer_pay_structure.id,
            'wage_type': 'hour'
            })

        # attendances to calc the worked hours
        self.env['hr.attendance'].create({
            'employee_id': self.richard_emp.id,
            'check_in': '2017-05-14 07:30:00',
            'check_out': '2017-05-14 17:00:00'
            })

        self.env['hr.attendance'].create({
            'employee_id': self.richard_emp.id,
            'check_in': '2017-05-17 07:30:00',
            'check_out': '2017-05-17 17:00:00'
            })

        # I create a payslip for "Richard"
        self.richard_payslip = self.env['hr.payslip'].create({
            'name': 'Payslip of Richard',
            'employee_id': self.richard_emp.id,
            'company_id': self.ref('base.main_company'),
            'contract_id': self.richard_contract.id,
            'date_from': '2017-05-01',
            'date_to': '2017-05-31'
            })

        # I create payroll config with company values
        self.configs = self.env['hr.payroll.config'].create({
            'ac_limit': 10500,
            'ac_per_off_limit': 1.0,
            'ac_per_in_limit': 1.1,
            'avs_per': 5.125,
            'pc_f_vd_per': 0.06,
            'fadmin_per': 0.25,
            'laa_per': 0.46,
            'lca_per': 0.52,
            'lpp_min': 2056.25,
            'lpp_max': 7050.00,
            'fa_amount_child': 250,
            'fa_amount_student': 330,
            'fa_min_number_childs': 3,
            'fa_amount_additional': 120
            })

    def test_no_lpp(self):
        _logger.debug(' -- Test NO LPP RATE w/ Hours -- ')

        # I click on 'Save' button on payroll configuration
        self.configs.save_configs()

        # compute worked hours based in attendances
        self.richard_payslip._compute_worked_hours()
        self.assertEqual(self.richard_payslip.worked_hours, 19)

        # I click on 'Compute Sheet' button on payslip
        self.richard_payslip.compute_sheet()

        rule_lines = self.richard_payslip.line_ids.search([
            ('salary_rule_id', 'in', self.rules_for_structure)
        ])

        _logger.debug('Test w/o LPP RATE w/ worked hours from attendance')

        for line in rule_lines:
            # BASIC CH
            if line.salary_rule_id.id == self.basic_ch:
                self.assertEqual(line.python_amount, 950)
                _logger.debug('BASIC CH %s' % line.python_amount)

            # GROSS CH
            if line.salary_rule_id.id == self.gross_ch:
                self.assertEqual(line.python_amount, 1900)

            # NET CH
            if line.salary_rule_id.id == self.net_ch:
                self.assertEqual(line.python_amount, 1630.98)

            # UI (AC)
            if line.salary_rule_id.id == self.ac_c:
                self.assertEqual(line.python_amount, 950)
                self.assertEqual(line.python_rate, -1.1)
                self.assertEqual(line.total, -10.45)
            if line.salary_rule_id.id == self.ac_e:
                self.assertEqual(line.python_amount, 950)
                self.assertEqual(line.python_rate, -1.1)
                self.assertEqual(line.total, -10.45)
            # UI (AC) - SOL
            if line.salary_rule_id.id == self.ac_c_sol:
                self.assertEqual(
                    line.python_amount, 0)
                self.assertEqual(line.python_rate, 0)
                self.assertEqual(line.total, 0)
            if line.salary_rule_id.id == self.ac_e_sol:
                self.assertEqual(
                    line.python_amount, 0)
                self.assertEqual(line.python_rate, 0)
                self.assertEqual(line.total, 0)

            # ALFA
            if line.salary_rule_id.id == self.alfa:
                self.assertEqual(line.python_amount, 950)
                self.assertEqual(line.python_rate, 100)
                self.assertEqual(line.total, 950)

            # IMP_SRC
            if line.salary_rule_id.id == self.imp_src:
                self.assertEqual(line.python_amount, 0)
                self.assertEqual(line.python_rate, 0)
                self.assertEqual(line.total, 0)

            # OAI (AVS)
            if line.salary_rule_id.id == self.avs_c:
                self.assertEqual(line.python_amount, 950)
                self.assertEqual(line.python_rate, -5.125)
                self.assertEqual(line.total, -48.69)
            if line.salary_rule_id.id == self.avs_e:
                self.assertEqual(line.python_amount, 950)
                self.assertEqual(line.python_rate, -5.125)
                self.assertEqual(line.total, -48.69)

            # AS Families (PC Famille)
            if line.salary_rule_id.id == self.pc_f_vd_c:
                self.assertEqual(line.python_amount, 950)
                self.assertEqual(line.python_rate, -0.06)
                self.assertEqual(line.total, -0.57)
            if line.salary_rule_id.id == self.pc_f_vd_e:
                self.assertEqual(line.python_amount, 950)
                self.assertEqual(line.python_rate, -0.06)
                self.assertEqual(line.total, -0.57)

            # AI (LAA)
            if line.salary_rule_id.id == self.laa_c:
                self.assertEqual(line.python_amount, 950)
                self.assertEqual(line.python_rate, -0.46)
                self.assertEqual(line.total, -4.37)
            if line.salary_rule_id.id == self.laa_e:
                self.assertEqual(line.python_amount, 950)
                self.assertEqual(line.python_rate, -0.46)
                self.assertEqual(line.total, -4.37)

            # SDA (LCA)
            if line.salary_rule_id.id == self.lca_c:
                self.assertEqual(line.python_amount, 950)
                self.assertEqual(line.python_rate, -0.52)
                self.assertEqual(line.total, -4.94)
            if line.salary_rule_id.id == self.lca_e:
                self.assertEqual(line.python_amount, 950)
                self.assertEqual(line.python_rate, -0.52)
                self.assertEqual(line.total, -4.94)

            # OBP (LPP)
            if line.salary_rule_id.id == self.lpp_c:
                self.assertEqual(line.python_amount, -200)
                self.assertEqual(line.python_rate, -100)
                self.assertEqual(line.total, -200)
            if line.salary_rule_id.id == self.lpp_e:
                self.assertEqual(line.python_amount, -200)
                self.assertEqual(line.python_rate, -100)
                self.assertEqual(line.total, -200)
