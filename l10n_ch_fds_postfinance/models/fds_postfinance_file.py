# -*- coding: utf-8 -*-
##############################################################################
#
#    Swiss Postfinance File Delivery Services module for Odoo
#    Copyright (C) 2015 Compassion CH
#    @author: Nicolas Tran
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
    journal_id = fields.Many2one(
        comodel_name='account.journal',
        related='directory_id.journal_id',
        string='journal',
        ondelete='restrict',
        help='default journal for this file'
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
        valid_files._sate_error_on()

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
    @api.one
    def import2bankStatements(self):
        ''' convert the file to a record of model bankStatment.

            :returns bool:
                - True if the convert was succeed
                - False otherwise
        '''
        try:
            values = {
                'journal_id': self.directory_id.journal_id.id,
                'data_file': self.data}
            bs_imoprt_obj = self.env['account.bank.statement.import']
            bank_wiz_imp = bs_imoprt_obj.create(values)
            import_result = bank_wiz_imp.import_file()
            # Mark the file as imported, remove binary as it should be
            # attached to the statement.
            self.write({
                'state': 'done',
                'data': None,
                'bank_statement_id':
                import_result['context']['statement_ids'][0]})
            _logger.info("[OK] import file '%s' to bank Statements",
                         (self.filename))
            return True
        except:
            _logger.warning("[FAIL] import file '%s' to bank Statements",
                            (self.filename))
            return False

    def _sate_error_on(self):
        ''' private function that change state to error

            :returns: None
        '''
        self.write({'state': 'error'})
