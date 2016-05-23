# -*- coding: utf-8 -*-
# © 2015-2016 David Coninckx (Open-Net Sarl)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import datetime
from openerp import fields
import openerp.tests.common as common


class TestPayroll(common.TransactionCase):
    def setUp(self):
        super(TestPayroll, self).setUp()
        self.employee = self.env['hr.employee'].create(
            {
                'name': 'TEST'
            }
        )

        self.working_schedule = self.env['resource.calendar'].create(
            {
                'name': 'Test schedule',
            }
        )

        self.contract = self.env['hr.contract'].create(
            {
                'name': "Test contract",
                'employee_id': self.employee.id,
                'working_hours': self.working_schedule.id,
                'wage': 0,
            }
        )
        res_cal_att_obj = self.env['resource.calendar.attendance']
        self.working_schedule_line = res_cal_att_obj.create(
            {
                'name': 'Monday',
                'dayofweek': '0',
                'hour_from': 8.0,
                'hour_to': 17.0,
                'time_increase': 0.1,
                'salary_increase': 0.1,
                'calendar_id': self.working_schedule.id,
            }
        )
        self.employee.working_hours = self.working_schedule.id

        sign_in_datetime = fields.Datetime.to_string(
            datetime.datetime(2016, 5, 23, 7, 0, 0))
        sign_out_datetime = fields.Datetime.to_string(
            datetime.datetime(2016, 5, 23, 16, 0, 0))

        self.attendance_sign_in = self.env['hr.attendance'].create(
            {
                'name': sign_in_datetime,
                'action': 'sign_in',
                'employee_id': self.employee.id,
            }
        )

        self.attendance_sign_out = self.env['hr.attendance'].create(
            {
                'name': sign_out_datetime,
                'action': 'sign_out',
                'employee_id': self.employee.id,
            }
        )

    def test_payslip(self):
        ps_date_from = fields.Date.to_string(
            datetime.date(2016, 5, 1)
        )
        ps_date_to = fields.Date.to_string(
            datetime.date(2016, 5, 31)
        )
        self.payslip = self.env['hr.payslip'].create(
            {
                'employee_id': self.employee.id,
                'contract_id': self.contract.id,
                'date_from': ps_date_from,
                'date_to': ps_date_to,
            }
        )
        self.payslip.compute_attendances()

        self.assertEqual(self.payslip.payslip_attendances[0].nb_days, 1)
        self.assertEqual(self.payslip.payslip_attendances[0].nb_hours, 8)
