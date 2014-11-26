# -*- coding: utf-8 -*-
#
#  File: migrations/8.0.1.0.08/pre-update-ir_model_data.py
#  Module: l10n_ch_hr_payroll
#
#  Created by cyp@open-net.ch
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

"""
Set the existings salary rules as non-updatable
This will ensure the update of this module won't try
to remove any existing rule not directly referenced.
This is necessary because some rules may be already in use.
"""


def migrate(cr, version):
    if not version:
        return

    query = ("UPDATE ir_model_data "
             "SET noupdate=true "
             "WHERE module='l10n_ch_hr_payroll' "
             "AND model='hr.salary.rule' ")
    cr.execute(query)
