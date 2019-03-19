# -*- coding: utf-8 -*-
# copyright 2018 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, api


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    @api.model
    def _get_line_key(self, line):
        return super(AccountPaymentOrder, self)._get_line_key(line) + (
            line.currency_id.name,
        )

    @api.model
    def generate_start_payment_info_block(
            self, parent_node, payment_info_ident,
            priority, local_instrument, category_purpose, sequence_type,
            requested_date, eval_ctx, gen_args):
        """ Replace the original Payment Identification (unique per file)
            in order to discriminate the records by currency"""
        payment_info_ident = (
            "self.name + '-' "
            "+ requested_date.replace('-', '') + '-' "
            "+ priority + '-' "
            "+ optional_args[0] + '-' "
            "+ local_instrument + '-' "
            "+ category_purpose"
        )
        return super(AccountPaymentOrder,
                     self).generate_start_payment_info_block(
            parent_node, payment_info_ident,
            priority, local_instrument, category_purpose, sequence_type,
            requested_date, eval_ctx, gen_args)

    @api.model
    def _has_detailed_address(self, gen_args):
        """
        Swiss PAIN flavors don't support address details nodes
        """
        if 'ch' in gen_args.get('pain_flavor'):
            return False
        return super(AccountPaymentOrder, self)._has_detailed_address(gen_args)
