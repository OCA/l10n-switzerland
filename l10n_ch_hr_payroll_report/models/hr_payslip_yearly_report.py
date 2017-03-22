# -*- coding: utf-8 -*-
# Copyright 2017 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo.addons.decimal_precision as dp

from odoo import tools
from odoo import models, fields


class HrPayslipYearlyReport(models.Model):
    _name = 'hr.payslip.yearly.report'
    _auto = False

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee'
    )

    code = fields.Char(
        string='Code',
    )
    name = fields.Char(
        string='Name',
    )
    code_and_name = fields.Char(
        string='Code and name',
    )
    year = fields.Char(
        string='Year',
    )
    month = fields.Selection(
        selection=[
            ('01', 'January'), ('02', 'February'), ('03', 'March'),
            ('04', 'April'), ('05', 'May'), ('06', 'June'),
            ('07', 'July'), ('08', 'August'), ('09', 'September'),
            ('10', 'October'), ('11', 'November'), ('12', 'December')
        ],
    )
    total = fields.Monetary(
        string='Total',
        digits=dp.get_precision('Payroll')
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency'
    )

    def init(self):
        tools.drop_view_if_exists(self._cr, 'hr_payslip_yearly_report')
        query = """CREATE or REPLACE VIEW hr_payslip_yearly_report as (
SELECT
    hpl.id AS id,
    hp.employee_id AS employee_id,
    hpl.code AS code,
    hpl.name AS name,
    hpl.code || ' - ' || hpl.name AS code_and_name,
    TO_CHAR(hp.date_from, 'YYYY') as year,
    TO_CHAR(hp.date_from, 'MM') as month,
    hpl.total AS total,
    c.currency_id AS currency_id
FROM
    hr_payslip_line hpl
INNER JOIN
    hr_payslip hp ON hpl.slip_id = hp.id
INNER JOIN
    res_company c ON hp.company_id = c.id
            )"""
        self._cr.execute(query)
