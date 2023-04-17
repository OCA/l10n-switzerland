# Copyright 2020 David Wulliamoz
# License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl).

from odoo import fields, models


class GenSdWizard(models.TransientModel):
    _name = "hr.salary.declaration.wizard"
    _description = "Generate salary declaration"

    date_from = fields.Date(string="Date from")
    date_to = fields.Date(string="Date to")

    def gen_sd(self):
        sd_obj = self.env["hr.salary.declaration"]
        sd_obj.generate_yearly_declaration(self.date_from, self.date_to)
