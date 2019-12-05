# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
import logging
from odoo.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)


class FdsPostfinanceFile(models.Model):
    _inherit = 'fds.postfinance.file'

    bank_statement_id = fields.Many2one(
        comodel_name='account.bank.statement',
        string='Bank Statement',
        ondelete='restrict',
        readonly=True,
    )

    @api.multi
    def import_to_bank_statement_button(self):
        """ convert the file to record of model bankStatment.
            Called by pressing import button.

            :return None:
        """
        valid_files = self.filtered(lambda f: f.state == 'draft')
        valid_files.import_to_bank_statements()

    @api.multi
    def import_to_bank_statements(self):
        """ convert the file to a record of model bankStatement."""
        try:
            values = {
                'data_file': self.data,
                'filename': self.filename
            }
            bs_import_obj = self.env['account.bank.statement.import']
            bank_wiz_imp = bs_import_obj.create(values)
            import_result = bank_wiz_imp.import_file()
            # Mark the file as imported, remove binary as it should be
            # attached to the statement.
            self.write({
                'state': 'done',
                'bank_statement_id':
                import_result['context']['statement_ids'][0],
                'error_message': False
            })
            _logger.info("[OK] import file '%s' to bank Statements",
                         self.filename)
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
                    'error_message': e.name or e.args and e.args[0]
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
