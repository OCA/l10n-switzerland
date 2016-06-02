# -*- coding: utf-8 -*-
# © 2016 Akretion (www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    bvr = fields.Boolean(
        compute='compute_bvr', readonly=True, string="BVR Payment")

    @api.multi
    def compute_bvr(self):
        for order in self:
            bvr = False
            for line in order.payment_line_ids:
                if line.communication_type == 'bvr':
                    bvr = True
                    break
            order.bvr = bvr

    @api.multi
    def compute_sepa_final_hook(self, sepa):
        self.ensure_one()
        sepa = super(AccountPaymentOrder, self).compute_sepa_final_hook(sepa)
        # BVR orders cannot be SEPA orders
        if sepa and self.bvr:
            sepa = False
        return sepa

    @api.multi
    def generate_pain_nsmap(self):
        self.ensure_one()
        nsmap = super(AccountPaymentOrder, self).generate_pain_nsmap()
        pain_flavor = self.payment_mode_id.payment_method_id.pain_version
        if pain_flavor == 'pain.001.001.03.ch.02':
            nsmap[None] = 'http://www.six-interbank-clearing.com/de/'\
                          'pain.001.001.03.ch.02.xsd'
        return nsmap

    @api.multi
    def generate_pain_attrib(self):
        self.ensure_one()
        pain_flavor = self.payment_mode_id.payment_method_id.pain_version
        if pain_flavor == 'pain.001.001.03.ch.02':
            attrib = {
                "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation":
                "http://www.six-interbank-clearing.com/de/"
                "pain.001.001.03.ch.02.xsd  pain.001.001.03.ch.02.xsd"
                }
            return attrib
        else:
            return super(AccountPaymentOrder, self).generate_pain_attrib()

    @api.model
    def generate_start_payment_info_block(
            self, parent_node, payment_info_ident,
            priority, local_instrument, sequence_type, requested_date,
            eval_ctx, gen_args):
        if gen_args.get('pain_flavor') == 'pain.001.001.03.ch.02' and self.bvr:
            local_instrument = 'CH01'
            gen_args['local_instrument_type'] = 'proprietary'
            gen_args['structured_remittance_issuer'] = False
        return super(AccountPaymentOrder, self).\
            generate_start_payment_info_block(
                parent_node, payment_info_ident, priority, local_instrument,
                sequence_type, requested_date, eval_ctx, gen_args)
