# -*- coding: utf-8 -*-
# © 2012-2016 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import _, api, exceptions, fields, models


class AccountMoveLine(models.Model):

    _inherit = "account.move.line"

    payment_slip_ids = fields.One2many(comodel_name='l10n_ch.payment_slip',
                                       inverse_name='move_line_id',
                                       string='Payment Slips',
                                       readonly=True)

    # Adding an index on invoice_id for the account.move.line.
    # The goal is to optimize the related field on payment_slip,
    # as updating the stored value will trigger a:
    #     self.env['account.move.line'].search([('invoice_id', '=', [xxx])])
    # for each invoice validation.
    invoice_id = fields.Many2one(
        'account.invoice', oldname="invoice", index=True
    )


class AccountInvoice(models.Model):
    """Inherit account.invoice in order to add bvr
    printing functionnalites. BVR is a Swiss payment vector"""

    _inherit = "account.invoice"

    reference = fields.Char(copy=False)

    partner_bank_id = fields.Many2one(
        'res.partner.bank',
        'Bank Account',
        help='The partner bank account to pay\n'
        'Keep empty to use the default'
    )

    bvr_reference = fields.Text(
        string='BVR ref',
        compute='_compute_full_bvr_name',
        store=True,
    )

    slip_ids = fields.One2many(
        string='Related slip',
        comodel_name='l10n_ch.payment_slip',
        inverse_name='invoice_id'
    )

    @api.depends('slip_ids', 'state')
    def _compute_full_bvr_name(self):
        """Concatenate related slip references

        :return: reference comma separated
        :rtype: str
        """
        for rec in self:
            if (rec.state not in ('open', 'paid') or
                    not rec.slip_ids):
                continue
            rec.bvr_reference = ', '.join(x.reference
                                          for x in rec.slip_ids
                                          if x.reference)

    def get_payment_move_line(self):
        """Return the move line related to current invoice slips

        :return: recordset of `account.move.line`
        :rtype: :py:class:`openerp.model.Models`
        """
        move_line_model = self.env['account.move.line']
        return move_line_model.search(
            [('move_id', '=', self.move_id.id),
             ('account_id.user_type_id.type', 'in',
              ['receivable', 'payable'])]
        )

    @api.model
    def _update_ref_on_account_analytic_line(self, ref, move_id):
        """Propagate reference on analytic line"""
        self.env.cr.execute(
            'UPDATE account_analytic_line SET ref=%s'
            '   FROM account_move_line '
            ' WHERE account_move_line.move_id = %s '
            '   AND account_analytic_line.move_id = account_move_line.id',
            (ref, move_id)
        )
        return True

    @api.model
    def _action_bvr_number_move_line(self, move_line, ref):
        """Propagate reference on move lines and analytic lines"""
        if not ref:
            return
        ref = ref.replace(' ', '')  # remove formatting
        self.env.cr.execute('UPDATE account_move_line SET transaction_ref=%s'
                            '  WHERE id=%s', (ref, move_line.id))
        self._update_ref_on_account_analytic_line(ref, move_line.move_id.id)
        self.env.invalidate_all()

    @api.multi
    def invoice_validate(self):
        """ Copy the BVR/ESR reference in the transaction_ref of move lines.

        For customers invoices: the BVR reference is computed using
        ``get_bvr_ref()`` on the invoice or move lines.

        For suppliers invoices: the BVR reference is stored in the reference
        field of the invoice.

        """
        pay_slip = self.env['l10n_ch.payment_slip']
        for inv in self:
            if inv.type in ('in_invoice', 'in_refund'):
                if inv.reference_type == 'bvr' and inv._check_bvr():
                    ref = inv.reference
                else:
                    ref = False
                move_lines = inv.get_payment_move_line()
                for move_line_id in move_lines:
                    self._action_bvr_number_move_line(move_line_id,
                                                      ref)
            else:
                for pay_slip in pay_slip.compute_pay_slips_from_invoices(inv):
                    ref = pay_slip.reference
                    self._action_bvr_number_move_line(pay_slip.move_line_id,
                                                      ref)
        return super(AccountInvoice, self).invoice_validate()

    @api.multi
    def print_bvr(self):
        self.ensure_one()
        self._check_bvr_generatable()
        self.sent = True
        return self.env['report'].get_action(
            self, 'l10n_ch_payment_slip.one_slip_per_page_from_invoice')

    @api.multi
    def _check_bvr_generatable(self):
        msg = []
        for inv in self:
            if inv.state in ('draft', 'cancel'):
                msg.append(_('The invoice must be confirmed.'))
            bank_acc = inv.partner_bank_id
            if not bank_acc:
                msg.append(_('The invoice needs a partner bank account.'))
            else:
                if not bank_acc.bvr_adherent_num:
                    msg.append(_('The bank account {} used in invoice has no '
                                 'BVR/ESR adherent number.'
                                 ).format(bank_acc.acc_number))
                if not (bank_acc.acc_type == 'postal' or bank_acc.ccp):
                    msg.append(_('The bank account {} used in invoice needs to'
                                 ' be a postal account or have a bank CCP.'
                                 ).format(bank_acc.acc_number))
            if msg:
                raise exceptions.UserError('\n'.join(msg))
