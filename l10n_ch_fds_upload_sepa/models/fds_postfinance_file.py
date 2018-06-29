# -*- coding: utf-8 -*-
# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64
import logging

from odoo import api, models, fields

_logger = logging.getLogger(__name__)


class FdsPostfinanceFile(models.Model):
    ''' Model of the information and files downloaded on FDS PostFinance
        (Keep files in the database)
    '''
    _inherit = 'fds.postfinance.file'

    payment_order = fields.Many2one(
        'account.payment.order',
        string='Payment order',
        ondelete='restrict',
        readonly=True,
    )

    @api.multi
    def import2bankStatements(self):
        account_pain002 = self.env['account.pain002.parser']
        pain_files = self.env[self._name]

        for pf_file in self:
            try:
                decoded_file = base64.b64decode(pf_file.data)

                result = account_pain002.parse(decoded_file)

                if result[0]:
                    if result[1] is not None and result[1].id:
                        # Link the payment order to the file import.
                        pf_file.payment_order = result[1].id
                        # Attach the file to the payment order.
                        self.env['ir.attachment'].create({
                            'datas_fname': pf_file.filename,
                            'res_model': 'account.payment.order',
                            'datas': pf_file.data,
                            'name': pf_file.filename,
                            'res_id': result[1].id})

                    pf_file.write({
                        'state': 'done',
                        'data': pf_file.data
                    })

                    _logger.info("[OK] import file '%s' as pain.000",
                                 pf_file.filename)

                    pain_files += pf_file
            except Exception as e:
                self.env.cr.rollback()
                self.env.invalidate_all()
                if pf_file.state != 'error':
                    pf_file.write({
                        'state': 'error',
                        'error_message': e.message or e.args and e.args[0]
                    })
                    # Here we must commit the error message otherwise it
                    # can be unset by a next file producing an error
                    # pylint: disable=invalid-commit
                    self.env.cr.commit()
                _logger.error("[FAIL] import file '%s' as pain 000",
                              (pf_file.filename), exc_info=True)

        return super(FdsPostfinanceFile,
                     self - pain_files).import2bankStatements()
