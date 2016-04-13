# -*- coding: utf-8 -*-
#
#  File: models/hr_payslip.py
#  Module: l10n_ch_payroll_attendances
#
#  Created by dco@open-net.ch
#
#  Copyright (c) 2015-TODAY Open-Net Ltd.
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

import datetime
from openerp import models, fields, api, workflow
import logging

_logger = logging.getLogger(__name__)

class Payslip(models.Model):
    _inherit = 'hr.payslip'

    auto_generated_holiday_ids = fields.One2many(
        comodel_name='hr.holidays',
        inverse_name='slip_id',
        string='Auto generated allocation request'
    )
    payslip_attendances = fields.One2many(
        comodel_name='hr.payslip.attendance',
        inverse_name='payslip_id',
        string='Computation of attendances',
        readonly=True, states={'draft': [('readonly', False)]}
    )

    def _total_seconds(self, time):
        return time.hour * 3600 + time.minute * 60 + time.second

    def _date_from_string(self, string_date):
        return fields.Date.from_string(string_date)

    def _datetime_from_string(self, string_date):
        return fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(string_date))

    def _time_from_hour_float(self, hour_float):
        return datetime.time(
            int(hour_float),
            int((hour_float % 1) * 60),
            0
        )

    def _date_is_in_period(self, date_in_period, date_from, date_to):
        if not date_in_period:
            return False
        if (date_from and date_in_period < date_from):
            return False
        if (date_to and date_in_period > date_to):
            return False
        return True

    def _is_fully_in_period(self, time1_from, time1_to, time2_from, time2_to):
        if (time1_from >= time2_from and time1_to <= time2_to):
            return True
        return False

    def _match_period(self, time1_from, time1_to, time2_from, time2_to):
        match_time_from = time1_from
        match_time_to = time1_to
        if (time1_to <= time2_from):
            return (False, False)
        if (time1_from < time2_from):
            match_time_from = time2_from
        if (time1_to > time2_to):
            match_time_to = time2_to
        return (match_time_from, match_time_to)

    def _clean_computation_result(self):
        payslip_attendance_obj = self.env['hr.payslip.attendance']
        payslip_attendance_to_remove = payslip_attendance_obj.search([
            ('payslip_id', '=', self.id)
        ])
        payslip_attendance_to_remove.unlink()

    def _compute_periodes_based_on_attendances(self, attendances):
        periodes = []
        attendances = sorted(
            attendances, key=lambda attendance: attendance.name
        )

        # Case the first attendance of the payslip periode is a sign_out
        if (attendances[0].action == 'sign_out'):
            date_from = self._datetime_from_string(self.date_from)
            date_to = self._datetime_from_string(attendances[0].name)
            periodes.append((date_from, date_to))
            attendances.pop(0)

        # Case the last attendance of the payslip periode is a sign_in
        if (attendances[-1].action == 'sign_in'):
            attendances.pop(-1)

        for attendance in attendances:
            if(attendance.action == 'sign_in'):
                index = attendances.index(attendance)
                date_from = self._datetime_from_string(attendance.name)
                date_to = self._datetime_from_string(
                    attendances[index + 1].name)

                if (date_to.date() != date_from.date()):
                    periodes.append((date_from, date_from.replace(
                        hour=23, minute=59, second=59
                    )))
                    periodes.append((date_to.replace(
                        hour=0, minute=0, second=0), date_to)
                    )
                else:
                    periodes.append((date_from, date_to))
        return periodes

    def _find_attendance_overlap_result(self, attendance, overlap):
        filtered_matches = []
        for match in overlap:
            if(match[0] == attendance or match[1] == attendance):
                filtered_matches.append(match)
        return filtered_matches

    def _search_overlap_cal_attendances(self, cal_attendances):
        match_results = []

        for i in xrange(0, len(cal_attendances)):
            cal_att_a = cal_attendances[i]
            hour_from_a = self._time_from_hour_float(cal_att_a.hour_from)
            hour_to_a = self._time_from_hour_float(cal_att_a.hour_to)

            for j in xrange(i + 1, len(cal_attendances)):
                cal_att_b = cal_attendances[j]
                if (cal_att_a != cal_att_b and
                        cal_att_a.dayofweek == cal_att_b.dayofweek):
                    hour_from_b = self._time_from_hour_float(
                        cal_att_b.hour_from)
                    hour_to_b = self._time_from_hour_float(
                        cal_att_b.hour_to)

                    match_result = self._match_period(
                        hour_from_a, hour_to_a,
                        hour_from_b, hour_to_b,
                    )
                    if match_result[0] and match_result[1]:
                        match_results.append(
                            (cal_att_a, cal_att_b, match_result)
                        )

        return match_results

    def _computation_result(self, periodes):
        overlap = self._search_overlap_cal_attendances(
            self.contract_id.working_hours.attendance_ids)

        for cal_attendance in self.contract_id.working_hours.attendance_ids:
            numberofday = 0
            seconds_present = 0

            for period in periodes:
                # Same day period
                if (period[0].date() == period[1].date() and
                        int(cal_attendance.dayofweek) == period[0].weekday()):
                    date_from = self._date_from_string(
                        cal_attendance.date_from)
                    date_to = self._date_from_string(
                        cal_attendance.date_to)

                    if self._date_is_in_period(
                            period[0].date(), date_from, date_to):
                        hour_from = self._time_from_hour_float(
                            cal_attendance.hour_from)
                        hour_to = self._time_from_hour_float(
                            cal_attendance.hour_to)

                        hour_from, hour_to = self._match_period(
                            period[0].time(), period[1].time(),
                            hour_from, hour_to
                        )

                        if hour_from and hour_to:
                            seconds_from = self._total_seconds(hour_from)
                            seconds_to = self._total_seconds(hour_to)
                            seconds_present += seconds_to - seconds_from

                            for match in self._find_attendance_overlap_result(
                                    cal_attendance, overlap):
                                match_date_from = (
                                    self._date_from_string(match[0].date_from),
                                    self._date_from_string(match[1].date_from)
                                )
                                if (self._date_is_in_period(
                                        match_date_from[0], period[0].date(),
                                        period[1].date()) or
                                        self._date_is_in_period(
                                            match_date_from[1],
                                            period[0].date(),
                                            period[1].date()
                                        )):
                                    match_period = (self._match_period(
                                        hour_from, hour_to,
                                        match[2][0], match[2][1]
                                    ))
                                    if not cal_attendance.exclude_period:
                                        sec_to = self._total_seconds(
                                            match_period[1])
                                        sec_from = self._total_seconds(
                                            match_period[0])
                                        seconds_present -= sec_to - sec_from
                            numberofday += 1

            if seconds_present > 0:
                vals = {
                    'name': cal_attendance.name,
                    'weekday': cal_attendance.dayofweek,
                    'payslip_id': self.id,
                    'time_increase': cal_attendance.time_increase,
                    'salary_increase': cal_attendance.salary_increase,
                    'nb_hours': seconds_present / 3600.0,
                    'nb_days': numberofday,
                    'hour_from': cal_attendance.hour_from,
                    'hour_to': cal_attendance.hour_to
                }
                self.env['hr.payslip.attendance'].create(vals)

    @api.multi
    def compute_allocation_requests(self):
        compensatory_days = 0

        for payslip_attendance in self.payslip_attendances:
            nb_hours = payslip_attendance.nb_hours
            time_inc = payslip_attendance.time_increase
            compensatory_days += (nb_hours * time_inc)

        leave_type = self.contract_id.working_hours.time_compensation_holiday_status

        holiday_obj = self.env['hr.holidays']
        holiday_request = holiday_obj.search([('slip_id', '=', self.id)])
        if (holiday_request):
            holiday_request.unlink()

        if (leave_type and compensatory_days > 0):
            vals = {
                'name': self.name,
                'type': 'add',
                'holiday_status_id': leave_type.id,
                'employee_id': self.employee_id.id,
                'holiday_type': 'employee',
                'number_of_days_temp': compensatory_days,
                'slip_id': self.id,
            }

            holiday_obj.create(vals)

    @api.multi
    def compute_attendances(self):
        self._clean_computation_result()
        res = True

        attendance_obj = self.env['hr.attendance']
        attendances = attendance_obj.search([
            ('employee_id', '=', self.employee_id.id),
            ('name', '>=', self.date_from),
            ('name', '<=', self.date_to)
        ])

        if attendances:
            periodes = self._compute_periodes_based_on_attendances(attendances)
            if (periodes):
                self._computation_result(periodes)
                self.compute_allocation_requests()
        return res

    @api.one
    def process_sheet(self):
        self._validate_autogen_holiday()
        return super(Payslip, self).process_sheet()

    def _validate_autogen_holiday(self):
        if self.auto_generated_holiday_ids:
            for auto_generated_holiday_id in self.auto_generated_holiday_ids:
                workflow.trg_validate(
                    self.env.user.id, 'hr.holidays',
                    auto_generated_holiday_id.id, 'validate',
                    self.env.cr
                )


class PayslipAttendance(models.Model):
    _name = "hr.payslip.attendance"

    @api.multi
    def _compute_tc(self):
        for attendance in self:
            attendance.time_compensation = attendance.time_increase * attendance.nb_hours

    @api.multi
    def _compute_sc(self):
        for attendance in self:
            attendance.salary_compensation = attendance.salary_increase * attendance.nb_hours * attendance.payslip_id.contract_id.hourly_rate_attendance

    name = fields.Char(string="Name")
    weekday = fields.Selection(selection=[
            ('0', 'Monday'),
            ('1', 'Tuesday'),
            ('2', 'Wednesday'),
            ('3', 'Thursday'),
            ('4', 'Friday'),
            ('5', 'Saturday'),
            ('6', 'Sunday')
        ], string="Week Day")
    hour_from = fields.Float(string="From")
    hour_to = fields.Float(string="To")
    nb_days = fields.Integer(string="Number of days")
    nb_hours = fields.Float(string="Number of hours")
    time_increase = fields.Float(string="Time compensation (%)")
    time_compensation = fields.Float(string="Time compensation", compute="_compute_tc")
    salary_increase = fields.Float(string="Wage compensation (%)")
    salary_compensation = fields.Float(string="Salary compensation", compute="_compute_sc")
    payslip_id = fields.Many2one(
        string="Linked to payslip", comodel_name='hr.payslip')
