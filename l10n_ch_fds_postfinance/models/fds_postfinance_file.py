# -*- coding: utf-8 -*-
# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api
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
        valid_files._state_error_on()

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
                values = {'data_file': pf_file.data}
                bs_import_obj = self.env['account.bank.statement.import']
                bank_wiz_imp = bs_import_obj.create(values)
                import_result = bank_wiz_imp.import_file()
                # Mark the file as imported, remove binary as it should be
                # attached to the statement.
                pf_file.write({
                    'state': 'done',
                    'data': None,
                    'bank_statement_id':
                    import_result['context']['statement_ids'][0]})
                _logger.info("[OK] import file '%s' to bank Statements",
                             (pf_file.filename))
            except:
                pf_file._state_error_on()
                _logger.warning("[FAIL] import file '%s' to bank Statements",
                                (pf_file.filename))
                res = False
        return res

    def _state_error_on(self):
        ''' private function that change state to error

            :returns: None
        '''
        self.write({'state': 'error'})
