# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64

from openerp.osv import osv


class email_template(osv.osv):
    _inherit = 'email.template'

    def generate_email_batch(self, cr, uid, template_id, res_ids, context=None, fields=None):
        """ Method overridden in order to add an attachment containing the QRR
        to the draft message when opening the 'send by mail' wizard on an invoice.
        This attachment generation will only occur if all the required data are
        present on the invoice. Otherwise, no attachment will be created, and
        the mail will only contain the invoice (as defined in the mother method).
        """
        rslt = super(email_template, self).generate_email_batch(
            cr, uid, template_id, res_ids, context=context, fields=fields)

        res_ids_to_templates = self.get_email_template_batch(
            cr, uid, template_id=template_id, res_ids=res_ids, context=context)
        for res_id in res_ids:
            template = res_ids_to_templates[res_id]
            related_model = template.model

            if related_model == 'account.invoice':
                report_name = template.report_name
                inv_record = self.pool.get(related_model).browse(cr, uid, res_id)
                inv_print_name = self.render_template(
                    cr, uid, report_name, related_model, res_id, context=context)
                new_attachments = []

                if inv_record.has_qrr():
                    # We add an attachment containing the QR-bill
                    qr_report_name = 'QR-bill-' + inv_print_name + '.pdf'
                    qr_pdf = self.ref('l10n_ch_qr_report').render_report(
                        cr, uid, [res_id], qr_report_name, False)
                    qr_pdf = base64.b64encode(qr_pdf)
                    new_attachments.append((qr_report_name, qr_pdf))

                attachments_list = rslt[res_id].get('attachments', False)
                if attachments_list:
                    attachments_list.extend(new_attachments)
                else:
                    rslt[res_id]['attachments'] = new_attachments
        return rslt
