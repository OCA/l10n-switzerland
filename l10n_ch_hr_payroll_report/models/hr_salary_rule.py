# -*- coding: utf-8 -*-
# Copyright 2017 Julien Coux (Camptocamp)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    report_is_total_rule = fields.Boolean(
        string='Is total rule',
    )

    report_display_details_columns = fields.Boolean(
        string='Display details columns',
        default=True,
    )

    report_is_net_amount = fields.Boolean(
        string='Is net amount',
    )
