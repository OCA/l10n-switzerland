from odoo import models, api

import base64
import logging

_logger = logging.getLogger(__name__)


class FdsPostfinanceFilePain000(models.Model):
    _inherit = 'fds.postfinance.file'

    @api.multi
    def import2bankStatements(self):

        account_pain000 = self.env['account.pain000.parser']
        pain_files = self.env[self._name]

        for pf_file in self:
            try:
                decoded_file = base64.b64decode(pf_file.data)

                result = account_pain000.parse(decoded_file)

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

        return super(FdsPostfinanceFilePain000,
                     self - pain_files).import2bankStatements()
