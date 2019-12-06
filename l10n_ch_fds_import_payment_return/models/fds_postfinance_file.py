# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
import logging
from odoo.addons.l10n_ch_payment_return_sepa.models.errors import\
    NoTransactionsError, FileAlreadyImported
from odoo.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)


class FdsPostfinanceFile(models.Model):
    _inherit = 'fds.postfinance.file'

    payment_return_id = fields.Many2one(
        comodel_name='payment.return',
        string='Payment Return',
        ondelete='restrict',
        readonly=True,
    )

    @api.multi
    def import_to_payment_return_button(self):
        """ convert the file to record of model payment return.
            Called by pressing import button.

            :return None:
        """
        valid_files = self.filtered(lambda f: f.state == 'draft')
        valid_files.import_to_payment_return()

    @api.multi
    def import_to_payment_return(self):
        """ convert the file to a record of model payment return."""
        try:
            values = {
                'data_file': self.data,
                'filename': self.filename
            }
            pr_import_obj = self.env['payment.return.import']
            pr_wiz_imp = pr_import_obj.create(values)
            import_result = pr_wiz_imp.import_file()
            # Mark the file as imported, remove binary as it should be
            # attached to the statement.
            self.write({
                'state': 'done',
                'payment_return_id':
                    import_result['res_id'],
                'payment_order': self.env['account.payment.order']
                .search([('name', '=',
                          import_result['context']['order_name'])]).id,
                'error_message': False
            })
            _logger.info("[OK] import file '%s'", self.filename)
        except NoTransactionsError as e:
            _logger.info(e.name, self.filename)
            self.write({
                'state': 'done',
                'payment_order': self.env['account.payment.order']
                .search([('name', '=', e.object[0]['order_name'])]).id,
                'error_message': e.name
            })
        except FileAlreadyImported as e:
            _logger.info(e.name, self.filename)
            references = [x['reference'] for x in e.object[0]['transactions']]
            payment_return = self.env['payment.return']\
                .search([('line_ids.reference', 'in', references)])
            self.write({
                'state': 'done',
                'payment_order': self.env['account.payment.order']
                .search([('name', '=', e.object[0]['order_name'])]).id,
                'payment_return_id': payment_return.id,
                'error_message': e.name
            })
        except UserError as e:
            # wrong parser used, raise the error to the parent so it's not
            # catch by the following except Exception
            raise e
        except Exception as e:
            self.env.cr.rollback()
            self.invalidate_cache()
            # Write the error in the postfinance file
            if self.state != 'error':
                self.write({
                    'state': 'error',
                    'error_message': e.args and e.args[0]
                })
                # Here we must commit the error message otherwise it
                # can be unset by a next file producing an error
                # pylint: disable=invalid-commit
                self.env.cr.commit()
            _logger.error(
                "[FAIL] import file '%s' to bank Statements",
                self.filename,
                exc_info=True
            )
