# -*- coding: utf-8 -*-
# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)


class FdsPostfinanceFile(models.Model):
    ''' Model of the information and files downloaded on FDS PostFinance
        (Keep files in the database)
    '''
    _name = 'fds.postfinance.file'

    fds_account_id = fields.Many2one(
        comodel_name='fds.postfinance.account',
        string='FDS account',
        ondelete='restrict',
        readonly=True,
        help='related FDS account'
    )
    data = fields.Binary(
        readonly=True,
        help='the downloaded file data'
    )
    bank_statement_id = fields.Many2one(
        comodel_name='account.bank.statement',
        string='Bank Statement',
        ondelete='restrict',
        readonly=True,
    )
    filename = fields.Char(
        readonly=True
    )
    directory_id = fields.Many2one(
        'fds.postfinance.directory',
        string='Directory',
        ondelete='restrict',
        readonly=True,
    )
    state = fields.Selection(
        selection=[('draft', 'Draft'),
                   ('done', 'Done'),
                   ('error', 'Error'),
                   ('cancel', 'Cancelled')],
        readonly=True,
        default='draft',
        help='state of file'
    )
    error_message = fields.Text()

    ##################################
    #         Button action          #
    ##################################
    @api.multi
    def import_button(self):
        ''' convert the file to record of model bankStatment.
            Called by pressing import button.

            :return None:
        '''
        valid_files = self.filtered(lambda f: f.state == 'draft')
        valid_files.import2bankStatements()

    @api.multi
    def change2error_button(self):
        ''' change the state of the file to error because the file is corrupt.
            Called by pressing 'corrupt file?' button.

            :return None:
        '''
        valid_files = self.filtered(lambda f: f.state == 'draft')
        valid_files.write({'state': 'error'})

    @api.multi
    def change2draft_button(self):
        ''' undo the file is corrupt to state draft.
            Called by pressing 'cancel corrupt file' button.

            :return None:
        '''
        self.write({'state': 'draft'})

    @api.multi
    def change2cancel_button(self):
        ''' Put file in cancel state.
            Called by pressing 'cancel' button.

            :return None:
        '''
        valid_files = self.filtered(lambda f: f.state in ('error', 'draft'))
        valid_files.write({'state': 'cancel'})

    ##############################
    #          function          #
    ##############################
    @api.multi
    def import2bankStatements(self):
        ''' convert the file to a record of model bankStatment.

            :returns bool:
                - True if the convert was succeed
                - False otherwise
        '''
        res = True
        for pf_file in self:
            try:
                values = {
                    'data_file': pf_file.data,
                    'filename': pf_file.filename
                }
                bs_import_obj = self.env['account.bank.statement.import']
                bank_wiz_imp = bs_import_obj.create(values)
                import_result = bank_wiz_imp.import_file()
                # Mark the file as imported, remove binary as it should be
                # attached to the statement.
                pf_file.write({
                    'state': 'done',
                    'bank_statement_id':
                    import_result['context']['statement_ids'][0]})
                _logger.info("[OK] import file '%s' to bank Statements",
                             (pf_file.filename))
            except Exception as e:
                self.env.cr.rollback()
                self.env.invalidate_all()
                # Write the error in the postfinance file
                if pf_file.state != 'error':
                    pf_file.write({
                        'state': 'error',
                        'error_message': e.message or e.args and e.args[0]
                    })
                    # Here we must commit the error message otherwise it
                    # can be unset by a next file producing an error
                    # pylint: disable=invalid-commit
                    self.env.cr.commit()
                _logger.error(
                    "[FAIL] import file '%s' to bank Statements",
                    pf_file.filename,
                    exc_info=True
                )
                res = False
        return res
