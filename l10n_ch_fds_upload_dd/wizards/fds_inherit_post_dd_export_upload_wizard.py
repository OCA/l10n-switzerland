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


class FdsInheritPostDdExportUploadWizard(models.TransientModel):
    ''' This addon allows you to upload the Direct Debit generated file to
        your FDS Postfinance.

        This addon will add an upload button to the DD wizard.
        This Class inherits from l10n_ch_lsv_dd.post_dd_export_wizard
    '''
    _inherit = 'post.dd.export.wizard'

    fds_account_id = fields.Many2one(
        comodel_name='fds.postfinance.account',
        string='FDS account',
        default=lambda self: self._get_default_account()
    )
    fds_directory_id = fields.Many2one(
        comodel_name='fds.postfinance.directory',
        string='FDS directory',
        help='Select one upload directory. Be sure to have at least one '
             'directory configured with upload access rights.'
    )
    state = fields.Selection(
        selection=[('create', 'Create'),
                   ('finish', 'finish'),
                   ('upload', 'upload'),
                   ('confirm', 'confirm')],
        readonly=True,
        default='create',
    )

    ##################################
    #         Button action          #
    ##################################
    @api.multi
    def upload_export_button(self):
        ''' Change the view to allow uploading the generated file into a
            FDS remote folder.

            :returns action: configuration for the next wizard's view
        '''
        self.ensure_one()
        self.state = 'upload'
        return self._refresh_wizard()

    @api.multi
    def send_export_button(self):
        ''' Upload pain_001 file to the FDS Postfinance by SFTP

            :returns action: configuration for wizard's next view
            :raises Warning:
                - If no FDS account and directory selected
                - If current user do not have key
                - If connection to SFTP fails
        '''
        self.ensure_one()
        if not self.fds_account_id:
            raise exceptions.Warning('Select a FDS account')

        if not self.fds_directory_id:
            raise exceptions.Warning('Select a directory')

        # check key of active user
        fds_keys_obj = self.env['fds.authentication.keys']
        key = fds_keys_obj.search([
            ['user_id', '=', self.env.uid],
            ['fds_account_id', '=', self.fds_account_id.id],
            ['key_active', '=', True]])

        if not key:
            raise exceptions.Warning(
                "You don't have access to the selected FDS account.")

        try:
            # create tmp file
            tmp_d = tempfile.mkdtemp()
            tmp_key = self._create_tmp_file(key.private_key_crypted, tmp_d)[0]
            tmp_f = self._create_tmp_file(self.file, tmp_d)[0]
            old_path_f = os.path.join(tmp_d, tmp_f.name)
            new_path_f = os.path.join(tmp_d, self.filename)
            shutil.move(old_path_f, new_path_f)
            key_pass = fds_keys_obj.config()

            # upload to sftp
            with pysftp.Connection(self.fds_account_id.hostname,
                                   username=self.fds_account_id.username,
                                   private_key=tmp_key.name,
                                   private_key_pass=key_pass) as sftp:
                with sftp.cd(self.fds_directory_id.name):
                    sftp.put(new_path_f)
                    _logger.info("[OK] upload file (%s) to SFTP",
                                 (self.filename))

            # change to initial name file (mandatory because of the close)
            shutil.move(new_path_f, old_path_f)
            self._state_confirm_on()
            self._add2historical()
        except Exception as e:
            _logger.error("Unable to connect to the SFTP: %s", e)
            raise exceptions.Warning('Unable to connect to the SFTP')

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

        return self._refresh_wizard()

    @api.multi
    def back_button(self):
        ''' Go back to the finish view.
            Called by pressing back button.

            :returns action: configuration for the next wizard's view
        '''
        self.ensure_one()
        self._state_finish_on()
        return self._refresh_wizard()

    @api.multi
    def close_button(self):
        self.ensure_one()
        self._state_finish_on()
        self.confirm_export()

    ##############################
    #          function          #
    ##############################
    def _get_default_account(self):
        """ Select one account if only one exists. """
        fds_accounts = self.env['fds.postfinance.account'].search([])
        if len(fds_accounts) == 1:
            return fds_accounts.id
        else:
            return False

    @api.onchange('fds_account_id')
    def _get_default_upload_directory(self):
        self.ensure_one()
        if self.fds_account_id:
            default_directory = self.fds_account_id.directory_ids.filtered(
                lambda d: d.name == 'debit-direct-upload' and
                d.allow_upload_file)
            if len(default_directory) == 1:
                self.fds_directory_id = default_directory

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
            'fds_account_id': self.fds_account_id.id,
            'filename': self.filename,
            'directory_id': self.fds_directory_id.id,
            'state': 'uploaded'}
        historical_dd_obj = self.env['fds.dd.upload.history']
        historical_dd_obj.create(values)

    @api.multi
    def _state_finish_on(self):
        ''' private function that changes state to finish

            :returns: None
        '''
        self.write({'state': 'finish'})

    @api.multi
    def _state_confirm_on(self):
        ''' private function that changes state to confirm

            :returns: None
        '''
        self.write({'state': 'confirm'})

    @api.multi
    def _refresh_wizard(self):
        ''' private function that refreshes the view of the current wizard.

            :returns action: action for reloading the current view.
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
