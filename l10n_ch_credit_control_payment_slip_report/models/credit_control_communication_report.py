# -*- coding: utf-8 -*-
from odoo import models, api


class ISRFromCreditControl(models.AbstractModel):
    _name = 'report.slip_from_credit_control'
    _description = 'Payment Slip from Credit Control'


class Report(models.Model):
    """Print pay slip form credit line"""

    _inherit = "report"

    @api.model
    def get_pdf(self, docids, report_name, html=None, data=None):
        reports = [
            'slip_from_credit_control',
            'slip_from_credit_control_communication',
        ]
        if report_name not in reports:
            return super(Report, self).get_pdf(
                docids, report_name, html, data
            )

        cr_line_obj = self.env['credit.control.line']
        slip_obj = self.env['l10n_ch.payment_slip']
        comm_obj = self.env['credit.control.communication']

        if report_name == 'slip_from_credit_control':
            credit_lines = cr_line_obj.browse(docids)
            communications = comm_obj._generate_comm_from_credit_lines(credit_lines)

        if report_name == 'slip_from_credit_control_communication':
            communications = comm_obj.browse(docids)

        control_lines_pdf = []
        for communication in communications:
            control_lines_pdf.append(super(Report, self).get_pdf(
                [communication.id],
                'account_credit_control.report_credit_control_summary',
                html,
                data,
            ))

            payment_slip_pdf = []
            for cr_line in communication.credit_control_line_ids:
                if not cr_line.move_line_id:
                    continue

                self = self.with_context(slip_credit_control_line_id=cr_line.id)
                slip = slip_obj.search([
                    ('move_line_id', '=', cr_line.move_line_id.id)
                ], limit=1)
                # generate ISR slip for each line
                payment_slip_pdf.append(super(Report, self).get_pdf(
                    slip.invoice_id.id,
                    'l10n_ch_payment_slip.one_slip_per_page_from_invoice',
                    html,
                    data,
                ))
            # attach ISR report to related communication report
            control_lines_pdf.extend(payment_slip_pdf)

        return self.merge_pdf_in_memory(control_lines_pdf)
