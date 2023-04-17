# Copyright 2023 Compassion Suisse
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Switzerland - export for electronic certificate",
    "summary": "Switzerland Payroll export",
    "category": "Localization",
    "author": "Odoo Community Association (OCA)",
    "depends": ["report_xml"],
    "version": "13.0.1.0.0",
    "auto_install": False,
    "demo": [],
    "website": "https://github.com/oca/l10n-switzerland",
    "license": "AGPL-3",
    "data": [
        "security/ir.model.access.csv",
        "views/hr_salary_declaration_view.xml",
        "report/yearly_payroll_certificate.xml",
        "views/generate_sd_wiz_view.xml",
    ],
    "installable": True,
}
