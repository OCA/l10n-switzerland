# -*- coding: utf-8 -*-
# Copyright 2017 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Switzerland - Payroll Reports",
    "summary": "Switzerland Payroll Reports",
    "version": "10.0.1.0.0",
    "category": "Reports",
    "website": "https://odoo-community.org/",
    "author": "Camptocamp, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "hr_payroll",
        "l10n_ch_hr_payroll",
    ],
    "data": [
        # Data
        "data/hr.salary.rule.xml",
        # Report
        "report/report_payslip.xml",
        # Security rules
        "security/ir.model.access.csv",
        # Views
        "views/hr_payslip_yearly_report.xml",
        "views/hr_salary_rule.xml",
        "views/menu.xml",
    ],
}
