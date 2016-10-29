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
                'time_compensation_holiday_status': 1,
            }
        )

        self.contract = self.env['hr.contract'].create(
            {
                'name': "Test contract",
                'employee_id': self.employee.id,
                'working_hours': self.working_schedule.id,
                'wage': 0,
                'hourly_rate_attendance': 120,
            }
        )
        res_cal_att_obj = self.env['resource.calendar.attendance']
        self.working_schedule_line1 = res_cal_att_obj.create(
            {
                'name': 'Monday',
                'dayofweek': '0',
                'hour_from': 8.0,
                'hour_to': 17.0,
                'date_from': '2016-05-23',
                'date_to': '2016-05-23',
                'time_increase': 0.1,
                'salary_increase': 0.1,
                'calendar_id': self.working_schedule.id,
                'exclude_period': True,
            }
        )
        self.working_schedule_line2 = res_cal_att_obj.create(
            {
                'name': 'Monday Night',
                'dayofweek': '0',
                'hour_from': 15.0,
                'hour_to': 20.0,
                'time_increase': 0.1,
                'salary_increase': 0.1,
                'calendar_id': self.working_schedule.id,
            }
        )

        self.employee.working_hours = self.working_schedule.id

        sign_in_past_month_datetime = fields.Datetime.to_string(
            datetime.datetime(2016, 4, 23, 7, 0, 0))
        sign_out_to_remove_datetime = fields.Datetime.to_string(
            datetime.datetime(2016, 5, 22, 16, 0, 0))
        sign_in_datetime = fields.Datetime.to_string(
            datetime.datetime(2016, 5, 23, 7, 0, 0))
        sign_out_datetime = fields.Datetime.to_string(
            datetime.datetime(2016, 5, 23, 16, 0, 0))

        self.env['hr.attendance'].create(
            {
                'name': sign_in_past_month_datetime,
                'action': 'sign_in',
                'employee_id': self.employee.id,
            }
        )
        self.env['hr.attendance'].create(
            {
                'name': sign_out_to_remove_datetime,
                'action': 'sign_out',
                'employee_id': self.employee.id,
            }
        )
        self.env['hr.attendance'].create(
            {
                'name': sign_in_datetime,
                'action': 'sign_in',
                'employee_id': self.employee.id,
            }
        )

        self.env['hr.attendance'].create(
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
        self.assertEqual(self.payslip.payslip_attendances[1].nb_days, 1)
        self.assertEqual(self.payslip.payslip_attendances[1].nb_hours, 1)
        self.assertEqual(
            self.payslip.payslip_attendances[0].time_compensation, 0.8)
        self.assertEqual(
            self.payslip.payslip_attendances[0].salary_compensation, 96)
        self.payslip.process_sheet()
