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

from openerp import models, fields, api, exceptions, _
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
                   ('error', 'Error')],
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
        self.ensure_one()

        self.import2bankStatements()

    @api.multi
    def change2error_button(self):
        ''' change the state of the file to error because the file is corrupt.
            Called by pressing 'corrupt file?' button.

            :return None:
        '''
        self.ensure_one()
        self._state_error_on()

    @api.multi
    def change2draft_button(self):
        ''' undo the file is corrupt to state draft.
            Called by pressing 'cancel corrupt file' button.

            :return None:
        '''
        self.state = 'draft'

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
        self.ensure_one()

        try:
            values = {
                'data_file': self.data}
            bs_import_obj = self.env['account.bank.statement.import']
            bank_wiz_imp = bs_import_obj.create(values)
            result = bank_wiz_imp.import_file()
            self.write({'bank_statement_id': result['context']['statement_ids'][0]})
            self._state_done_on()
            self._add_bankStatement_ref()
            self._remove_binary_file()
            _logger.info("[OK] import file '%s' to bank Statements",
                         (self.filename))
            return True
        except:
            self._state_error_on()
            _logger.warning("[FAIL] import file '%s' to bank Statements",
                            (self.filename))
            return False

    @api.multi
    def _remove_binary_file(self):
        ''' private function that remove the binary file.
            the binary file is already convert to bank statment attachment.

            :returns None:
        '''
        self.write({'data': None})

    @api.multi
    def _state_done_on(self):
        ''' private function that change state to done

            :returns: None
        '''
        self.ensure_one()
        self.write({'state': 'done'})

    @api.multi
    def _state_error_on(self):
        ''' private function that change state to error

            :returns: None
        '''
        self.ensure_one()
        self.write({'state': 'error'})
