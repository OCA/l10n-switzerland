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

import logging
import base64
import tempfile
import shutil
import pysftp
import os

from openerp import models, fields, api, exceptions

_logger = logging.getLogger(__name__)


class fds_files_import_tobankstatments_wizard(models.TransientModel):
    ''' This wizard checks and downloads files in FDS Postfinance server
        that were not already downloaded on the database.
        This wizard is called when we choose the update_fds for one FDS.
    '''
    _name = 'fds.files.import.tobankstatments.wizard'

    msg_file_imported = fields.Char(
        'Imported files',
        readonly=True
    )
    msg_import_file_fail = fields.Char(
        'File import failures',
        readonly=True
    )
    msg_exist_file = fields.Char(
        'Files already existing',
        readonly=True
    )
    state = fields.Selection(
        selection=[('default', 'Default'),
                   ('done', 'Done'),
                   ('error', 'Error Permission'),
                   ('errorSFTP', 'Error SFTP')],
        readonly=True,
        default='default',
        help='[Info] keep state of the wizard'
    )

    ##################################
    #         Button action          #
    ##################################
    @api.multi
    def import_button(self):
        ''' download the file from the sftp where the directories
            were selected in the FDS configuration, and if possible import
            to bank Statments.
            Called by pressing import button.

            :returns action: configuration for the next wizard's view
        '''
        self.ensure_one()
        (fds_id, hostname, username, key, key_pass) = self._get_sftp_config()
        if not key:
            self.state = 'error'
            return self._do_populate_tasks()

        if not key.key_active:
            self.state = 'error'
            return self._do_populate_tasks()

        try:
            # create temp file
            (tmp_key, tmp_d) = self._create_tmp_file(key.private_key_crypted)

            # get name of directory where download
            dir = [(e.name, e.id) for e in
                   fds_id.directory_ids
                   if e.allow_download_file is True]

            # connect sftp
            with pysftp.Connection(hostname,
                                   username=username,
                                   private_key=tmp_key.name,
                                   private_key_pass=key_pass) as sftp:

                fds_files_ids = self._download_file(sftp, dir, tmp_d, fds_id)

            # import to bank statements
            self._import2bankStatements(fds_files_ids)
            self.state = 'done'
        except Exception as e:
            self.state = 'errorSFTP'
            _logger.error("Unable to connect to the sftp: %s", e)
        finally:
            try:
                tmp_key.close()
            except:
                _logger.error("remove tmp_key file failed")
            try:
                shutil.rmtree(tmp_d)
            except:
                _logger.error("remove tmp directory failed")

        self._changeMessage()
        return self._do_populate_tasks()

    ##############################
    #          function          #
    ##############################
    @api.multi
    def _download_file(self, sftp, directories, tmp_directory, fds_id):
        ''' private function that downloads files from the sftp server where
            the directories were selected in the configuration of FDS.

            :param (obj, (str, str), str, record:
                - pysftp object
                - (directory name, directory id) from fds.pf.files.directory
                - tmp directory name
                - fds account
            :returns recordset: of download files (model fds.postfinance.files)
        '''
        fds_files_ids = self.env['fds.postfinance.files']
        for d in directories:
            (dir_name, dir_id) = (d[0], d[1])

            with sftp.cd(dir_name):
                list_name_files = sftp.listdir()
            sftp.get_d(dir_name, tmp_directory)
            _logger.info("[OK] download files in '%s' ", (dir_name))

            for nameFile in list_name_files:
                # check if file exist already
                if not fds_files_ids.search([['filename', '=', nameFile]]):
                    # save in the model fds_postfinance_files
                    path = os.path.join(tmp_directory, nameFile)
                    with open(path, "rb") as f:
                        file_data = f.read()
                    values = {
                        'fds_account_id': fds_id.id,
                        'data': base64.b64encode(file_data),
                        'filename': nameFile,
                        'directory_id': dir_id}
                    fds_files_ids += fds_files_ids.create(values)
                else:
                    self.msg_exist_file += nameFile + "; "
                    _logger.warning("[FAIL] file '%s' already exist",
                                    (nameFile))

        return fds_files_ids

    @api.multi
    def _import2bankStatements(self, fds_files_ids):
        ''' private function that import the files to bank statments

            :param recordset: of model fds_postfinance_files
            :returns None:
        '''
        for fds_file in fds_files_ids:
            if fds_file.import2bankStatements():
                self.msg_file_imported += fds_file.filename + "; "
            else:
                self.msg_import_file_fail += fds_file.filename + "; "

    @api.multi
    def _get_sftp_config(self):
        ''' private function that get the sftp configuration need for
            connection with the server.

            :returns (record, str, str, str, str):
                - record of model fds.postfinance.account
                - hostname, username, password, key pass
            :returns action: if no key found, return error wizard's view
            :raises Warning:
                - if many FDS account selected
        '''
        # get selected fds_postfiance_account id
        active_ids = self.env.context.get('active_ids')
        if len(active_ids) != 1:
            raise exceptions.Warning('Select only one FDS account')
        fds_account = self.env['fds.postfinance.account'].browse(active_ids[0])

        # check key of active user
        fds_authentication_key_obj = self.env['fds.authentication.keys']
        key = fds_authentication_key_obj.search([
            ['user_id', '=', self.env.uid],
            ['fds_account_id', '=', fds_account.id]])

        # get username, hostname, key_pass
        hostname = fds_account.hostname
        username = fds_account.username
        key_pass = fds_authentication_key_obj.config()

        return (fds_account, hostname, username, key, key_pass)

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
    def _changeMessage(self):
        ''' private function that change message to none if no message

            :returns None:
        '''
        if self.msg_exist_file == '':
            self.msg_exist_file = 'none'
        if self.msg_file_imported == '':
            self.msg_file_imported = 'none'
        if self.msg_import_file_fail == '':
            self.msg_import_file_fail = 'none'

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

    @api.multi
    def _close_wizard(self):
        ''' private function that put action wizard to close.

            :returns action: close the wizard's view
        '''
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
