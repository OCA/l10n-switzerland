# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import UserError


class CreditControlPrinter(models.TransientModel):
    _inherit = "credit.control.printer"

    def print_lines(self):
        self.ensure_one()
        comm_obj = self.env["credit.control.communication"]
        if not self.line_ids:
            raise UserError(_("No credit control lines selected."))

        lines = self._get_lines(self.line_ids, self._credit_line_predicate)

        comms = comm_obj._generate_comm_from_credit_lines(lines)

        if self.mark_as_sent:
            comms._mark_credit_line_as_sent()

        report_name = "account_credit_control.report_credit_control_summary"
        report_obj = self.env["ir.actions.report"]._get_report_from_name(report_name)
        return report_obj.report_action(comms)
