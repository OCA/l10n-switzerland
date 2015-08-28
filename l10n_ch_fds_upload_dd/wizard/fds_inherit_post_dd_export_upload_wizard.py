# -*- coding: utf-8 -*-
##############################################################################
#
#    Swiss Postfinance File Delivery Services module for Odoo
#    Copyright (C) 2014 Compassion CH
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

from openerp import models, fields, api, exceptions
import logging
import base64
import tempfile
import shutil
import pysftp
import os

_logger = logging.getLogger(__name__)


class fds_inherit_post_dd_export_upload_wizard(models.TransientModel):
    ''' This addon allows you to upload the Direct Debit geberate file to
        your FDS Postfinance.

        This addon will add upload button to the DD wizard.
        This Class inherit from l10n_ch_lsv_dd.post_dd_export_wizard
    '''
    _inherit = 'post.dd.export.wizard'

    fds_account_directory = fields.Many2one(
        comodel_name='fds.postfinance.files.directory',
        string='FDS files directory',
        help='select one upload directory or config your upload directory'
    )
    state = fields.Selection(
        selection=[('create', 'Create'),
                   ('finish', 'finish'),
                   ('upload', 'upload'),
                   ('confirm', 'confirm')],
        readonly=True,
        default='create',
        help='[Info] keep state of the wizard'
    )
    fds_account = fields.Many2one(
        comodel_name='fds.postfinance.account',
        string='FDS account',
        help='select one FDS account or create a FDS account'
    )

    ##################################
    #         Button action          #
    ##################################
    @api.multi
    def upload_export_button(self):
        ''' change the view to the wizard or directly upload the file if
            only one FDS account and only one upload directory selected.
            Called by pressing upload button.

            :returns action: configuration for the next wizard's view
        '''
        self.ensure_one()

        # check if only one fds account
        existing_account_ids = self.fds_account.search([]).ids
        if len(existing_account_ids) != 1:
            self._state_upload_on()
            return self._do_populate_tasks()

        self.fds_account = existing_account_ids[0]

        # check if default upload directory exist
        if not self.fds_account.upload_dd_directory:
            self._state_upload_on()
            return self._do_populate_tasks()

        # check if default upload directory is allowed
        dir_name = self.fds_account.upload_dd_directory.name
        dir = self.fds_account_directory.search([('name', '=', dir_name)])
        if not dir.allow_upload_file:
            self._state_upload_on()
            return self._do_populate_tasks()

        self.fds_account_directory = self.fds_account.upload_dd_directory
        return self.send_export_button()

    @api.multi
    def send_export_button(self):
        ''' upload pain_001 file to the FDS Postfinance by sftp

            :returns action: configuration for the next wizard's view
            :raises Warning:
                - If no fds account and directory selected
                - if current user do not have key
                - if connection to sftp cannot
        '''
        self.ensure_one()
        if not self.fds_account:
            raise exceptions.Warning('Select a FDS account')

        if not self.fds_account_directory:
            raise exceptions.Warning('Select a directory')

        # check key of active user
        fds_authentication_key_obj = self.env['fds.authentication.keys']
        key = fds_authentication_key_obj.search([
            ['user_id', '=', self.env.user.id],
            ['fds_account_id', '=', self.fds_account.id]])

        if not key:
            raise exceptions.Warning('You don\'t have key')

        if not key.active_key:
            raise exceptions.Warning('Key not active')

        try:
            # create tmp file
            tmp_d = tempfile.mkdtemp()
            tmp_key = self._create_tmp_file(key.private_key_crypted, tmp_d)[0]
            tmp_f = self._create_tmp_file(self.file, tmp_d)[0]
            old_path_f = os.path.join(tmp_d, tmp_f.name)
            new_path_f = os.path.join(tmp_d, self.filename)
            shutil.move(old_path_f, new_path_f)
            key_pass = fds_authentication_key_obj.config()

            # upload to sftp
            with pysftp.Connection(self.fds_account.hostname,
                                   username=self.fds_account.username,
                                   private_key=tmp_key.name,
                                   private_key_pass=key_pass) as sftp:
                with sftp.cd(self.fds_account_directory.name):
                    sftp.put(new_path_f)
                    _logger.info("[OK] upload file (%s) to sftp",
                                 (self.filename))

            # change to initial name file (mandatory because of the close)
            shutil.move(new_path_f, old_path_f)
            self._state_confirm_on()
            self._add2historical()
        except Exception as e:
            _logger.error("Unable to connect to the sftp: %s", e)
            raise exceptions.Warning('Unable to connect to the sftp')

        finally:
            try:
                tmp_key.close()
            except:
                _logger.error("remove tmp_key file failed")
            try:
                tmp_f.close()
            except:
                _logger.error("remove tmp_f file failed")
            try:
                shutil.rmtree(tmp_d)
            except:
                _logger.error("remove tmp directory failed")

        return self._do_populate_tasks()

    @api.multi
    def back_button(self):
        ''' Go back to the finish view.
            Called by pressing back button.

            :returns action: configuration for the next wizard's view
        '''
        self.ensure_one()
        self._state_finish_on()
        return self._do_populate_tasks()

    @api.multi
    def close_button(self):
        self.ensure_one()
        self._state_finish_on()
        self.confirm_export()

    ##############################
    #          function          #
    ##############################
    @api.multi
    def _create_tmp_file(self, data, tmp_directory=None):
        ''' private function that write data to a tmp file and if no tmp
            directory use, create one.

            :param str data: data in base64 format
            :param str tmp_directory: path of the directory
            :returns (obj file, str directory): obj of type tempfile
        '''
        self.ensure_one()
        try:
            if not tmp_directory:
                tmp_directory = tempfile.mkdtemp()

            tmp_file = tempfile.NamedTemporaryFile(dir=tmp_directory)
            tmp_file.write(base64.b64decode(data))
            tmp_file.flush()
            return (tmp_file, tmp_directory)
        except Exception as e:
            _logger.error("Bad handling tmp in fds_inherit_sepa_wizard: %s", e)

    @api.multi
    def _add2historical(self):
        ''' private function that add the upload file to historic

            :returns: None
        '''
        self.ensure_one()
        values = {
            'banking_export_id': self.banking_export_ch_dd_id.id,
            'fds_account_id': self.fds_account.id,
            'filename': self.filename,
            'directory_id': self.fds_account_directory.id,
            'state': 'uploaded'}
        historical_dd_obj = self.env['fds.postfinance.historical.dd']
        historical_dd_obj.create(values)

    @api.multi
    def _state_finish_on(self):
        ''' private function that change state to finish

            :returns: None
        '''
        self.ensure_one()
        self.write({'state': 'finish'})

    @api.multi
    def _state_upload_on(self):
        ''' private function that change state to upload

            :returns: None
        '''
        self.ensure_one()
        self.write({'state': 'upload'})

    @api.multi
    def _state_confirm_on(self):
        ''' private function that change state to confirm

            :returns: None
        '''
        self.ensure_one()
        self.write({'state': 'confirm'})

    @api.multi
    def _do_populate_tasks(self):
        ''' private function that continue with the same wizard.

            :returns action: configuration for the next wizard's view
        '''
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': self.id,
            'target': 'new',
        }
        return action
