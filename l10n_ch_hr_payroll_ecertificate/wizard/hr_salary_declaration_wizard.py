# Copyright 2020 David Wulliamoz
# License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl).

from odoo import fields, models


class GenSdWizard(models.TransientModel):
    _name = "hr.salary.declaration.wizard"
    _description = "Generate salary declaration"

    date_from = fields.Date(string="Date from")
    date_to = fields.Date(string="Date to")
    gross_income = fields.Many2one("hr.salary.rule", string="Gross income / N°8")
    lpp_bvg = fields.Many2one("hr.salary.rule", string="BVG/LPP / N°10.1")
    company_car = fields.Many2one(
        "hr.salary.rule", string="Private use of company car / N°2.2"
    )
    deduction = fields.Many2one("hr.salary.rule", string="Total deduction / N°9")

    def gen_sd(self):
        sd_obj = self.env["hr.salary.declaration"]
        sd_obj.generate_yearly_declaration(
            self.date_from,
            self.date_to,
            self.company_car,
            self.gross_income,
            self.deduction,
            self.lpp_bvg,
        )
