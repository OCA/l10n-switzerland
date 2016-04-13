# -*- coding: utf-8 -*-
#
#  File: models/res_calendar.py
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


from openerp import models, fields


class Calendar(models.Model):
    _inherit = 'resource.calendar'

    time_compensation_holiday_status = fields.Many2one(
        string="Time compensation destination",
        comodel_name='hr.holidays.status')


class CalendarAttendances(models.Model):
    _inherit = 'resource.calendar.attendance'

    time_increase = fields.Float(string="Time compensation (%)")
    salary_increase = fields.Float(string="Wage compensation (%)")
    exclude_period = fields.Boolean(string="Exclusive")
