# Copyright 2023 David Wulliamoz
# License AGPL-3.0 or later (https://www.gnuorg/licenses/agpl).

import logging
import math
from collections import defaultdict

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HrSalaryDeclaration(models.Model):
    _name = "hr.salary.declaration"
    _description = "Salary declaration for generating xml"

    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee")
    date_from = fields.Date()
    date_to = fields.Date()
    grossincome = fields.Integer()
    social_ded = fields.Integer()
    bvg_lpp_ded = fields.Integer()
    year = fields.Char()

    @api.model
    def generate_yearly_declaration(self, date_from, date_to):
        payslip_lines = self.env["hr.payslip.line"].search(
            [
                ("slip_id.date_from", ">=", date_from),
                ("slip_id.date_to", "<=", date_to),
                ("slip_id.state", "=", "done"),
            ]
        )
        employee_ids = payslip_lines.mapped("employee_id.id")
        grossincome = defaultdict(float)
        social_ded = defaultdict(float)
        bvg_lpp_ded = defaultdict(float)
        d_from = defaultdict(str)
        d_to = defaultdict(str)
        for line in payslip_lines:
            if line.code == "5000":
                grossincome[line.employee_id.id] += line.total
            if line.name == "OBP Employee":
                bvg_lpp_ded[line.employee_id.id] -= line.total
            if line.code == "TOTAL_DED":
                social_ded[line.employee_id.id] -= line.total
            if (
                line.slip_id.date_from.strftime("%Y-%m-%d")
                < d_from[line.employee_id.id]
                or not d_from[line.employee_id.id]
            ):
                d_from[line.employee_id.id] = line.slip_id.date_from.strftime(
                    "%Y-%m-%d"
                )
            if (
                line.slip_id.date_to.strftime("%Y-%m-%d") > d_to[line.employee_id.id]
                or not d_to[line.employee_id.id]
            ):
                d_to[line.employee_id.id] = line.slip_id.date_to.strftime("%Y-%m-%d")
        _logger.info("generating '%s' salary declaration", len(employee_ids))
        for emp in employee_ids:
            sd_vals = {
                "employee_id": emp,
                "date_from": d_from[emp],
                "date_to": d_to[emp],
                "grossincome": math.floor(grossincome[emp]),
                "social_ded": math.ceil(social_ded[emp] - bvg_lpp_ded[emp]),
                "bvg_lpp_ded": math.ceil(bvg_lpp_ded[emp]),
                "year": date_to.strftime("%Y-%m-%d")[:4],
            }
            self.create(sd_vals)
