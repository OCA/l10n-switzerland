# Copyright 2012-2019 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, api, fields, _
from odoo.tools import mod10r
from odoo import exceptions


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    reference_type = fields.Selection(
        selection_add=[('isr', 'ISR Reference')])

    def _search(self, args, offset=0, limit=None, order=None, count=False,
                access_rights_uid=None):
        domain = []
        for arg in args:
            if not isinstance(arg, (tuple, list)) or len(arg) != 3:
                domain.append(arg)
                continue
            field, operator, value = arg
            if field != 'reference':
                domain.append(arg)
                continue
            if operator not in ('like', 'ilike', '=like', '=ilike',
                                'not like', 'not ilike'):
                domain.append(arg)
                continue
            if value:
                value = value.replace(' ', '')
                if not value:
                    # original value contains only spaces, the query
                    # would return all rows, so avoid a costly search
                    # and drop the domain triplet
                    continue
                # add wildcards for the like search, except if the operator
                # is =like of =ilike because they are supposed to be there yet
                if operator.startswith('='):
                    operator = operator[1:]
                else:
                    value = '%%%s%%' % (value,)
            # add filtered operator to query
            query_op = ("SELECT id FROM account_invoice "
                        "WHERE REPLACE(reference, ' ', '') %s %%s" %
                        (operator,))
            # avoid pylint check on no-sql-injection query_op is safe
            query = query_op
            self.env.cr.execute(query, (value,))
            ids = [t[0] for t in self.env.cr.fetchall()]
            domain.append(('id', 'in', ids))

        return super()._search(
            domain, offset=offset, limit=limit, order=order, count=count,
            access_rights_uid=access_rights_uid)

    @api.onchange('reference')
    def onchange_reference(self):
        """Identify if the reference entered is of type ISR
        if it does, change reference_type"""
        if len(self.reference or '') == 27:
            try:
                self._is_isr_reference()
            except exceptions.ValidationError:
                return
            self.reference_type = 'isr'

    @api.constrains('reference_type')
    def _check_bank_type_for_type_isr(self):
        for invoice in self:
            if invoice.reference_type == 'isr':
                bank_acc = invoice.partner_banks_to_show()
                if not (bank_acc.acc_type == 'postal' or
                        bank_acc.acc_type != 'postal' and
                        (bank_acc.ccp or bank_acc.bank_id.ccp)):
                    raise exceptions.ValidationError(
                        _("Bank account shouldn't be empty, for IRS reference "
                          "type, you can set it manually or set appropriate"
                          " payment mode.")
                    )
        return True

    @api.multi
    def _is_isr_reference(self):
        """
        Function to validate a ISR reference like :
        0100054150009>132000000000000000000000014+ 1300132412>
        The validation is based on l10n_ch
        """
        if not self.reference:
            raise exceptions.ValidationError(
                _('ISR Reference is required')
            )
        # In this case
        # <010001000060190> 052550152684006+ 43435>
        # the reference 052550152684006 do not match modulo 10
        #
        if (mod10r(self.reference[:-1]) != self.reference and
                len(self.reference) == 15):
            return True
        #
        if mod10r(self.reference[:-1]) != self.reference:
            raise exceptions.ValidationError(
                _('Invalid ISR Number (wrong checksum).')
            )

    @api.constrains('reference')
    def _check_isr(self):
        """ Do the check only for invoice with reference_type = 'isr' """
        for invoice in self:
            if invoice.reference_type == 'isr':
                invoice._is_isr_reference()
        return True

    def partner_banks_to_show(self):
        """
        Extend method from account_payment_partner to add specific
        logic for switzerland bank payments if base method does not give
        a result
        """
        res = super().partner_banks_to_show()
        if not res:
            if self.journal_id:
                return self.journal_id.bank_account_id
        return res
