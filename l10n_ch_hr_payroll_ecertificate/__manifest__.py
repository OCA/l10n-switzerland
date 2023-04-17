# Copyright 2021 Compassion Suisse
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Switzerland - export for electronic certificate",
    "summary": "Switzerland Payroll export",
    "category": "Localization",
    "author": "Compassion Suisse,Odoo Community Association (OCA)",
    "depends": ["report_xml"],
    "version": "12.0.1.0.0",
    "auto_install": False,
    "demo": [],
    "website": "http://compassion.ch",
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "views/hr_salary_declaration_view.xml",
        "report/yearly_payroll_certificate.xml",
        "wizzards/generate_sd_wiz_view.xml",
    ],
    "installable": True,
}
