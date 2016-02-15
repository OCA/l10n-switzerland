# -*- coding: utf-8 -*-
# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import base64
import logging
import os
import shutil
import tempfile
import traceback

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)

try:
    import pysftp
    SFTP_OK = True
except ImportError:
    SFTP_OK = False
    _logger.error(
        'This module needs pysftp to connect to the FDS. '
        'Please install pysftp on your system. (sudo pip install pysftp)'
    )


class FdsFilesImportToBankStatementsWizard(models.TransientModel):
    ''' This wizard checks and downloads files in FDS Postfinance server
        that were not already downloaded on the database.
        This wizard is called when we choose the update_fds for one FDS.
    '''
    _name = 'fds.files.import.tobankstatments.wizard'

    fds_account_id = fields.Many2one(
        'fds.postfinance.account',
        'FDS Account',
        required=True,
        default=lambda self: self._get_fds_account()
    )
    msg_file_imported = fields.Char(
        'Imported files',
        readonly=True,
        default=''
    )
    msg_import_file_fail = fields.Char(
        'File import failures',
        readonly=True,
        default=''
    )
    msg_exist_file = fields.Char(
        'Files already existing',
        readonly=True,
        default=''
    )
    msg_import_file_ignore = fields.Char(
        'Files ignored',
        readonly=True,
        default=''
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
        if not SFTP_OK:
            raise UserError(_("Please install pysftp to use this feature."))
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
            dir = fds_id.directory_ids.filtered('allow_download_file')

            # connect sftp
            with pysftp.Connection(
                    hostname,
                    username=username,
                    private_key=tmp_key.name,
                    private_key_pass=key_pass) as sftp:

                fds_files_ids = self._download_file(sftp, dir, tmp_d, fds_id)

            # import to bank statements
            self._import2bankStatements(fds_files_ids)
            self.state = 'done'
        except Exception:
            self.env.cr.rollback()
            self.env.invalidate_all()
            self.state = 'errorSFTP'
            _logger.error(traceback.print_exc())
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
    def _get_fds_account(self):
        # get selected fds_postfinance_account id
        account_obj = self.env['fds.postfinance.account']
        active_ids = self.env.context.get('active_ids')
        if active_ids and len(active_ids) == 1:
            return account_obj.browse(active_ids[0])
        fds_account = account_obj.search([], limit=1)
        return fds_account

    @api.multi
    def _download_file(self, sftp, directories, tmp_directory, fds_id):
        ''' private function that downloads files from the sftp server where
            the directories were selected in the configuration of FDS.

            :param (obj, (str, str), str, record:
                - pysftp object
                - directories from fds.pf.files.directory
                - tmp directory name
                - fds account
            :returns recordset: of download files (model fds.postfinance.file)
        '''
        fds_files_ids = self.env['fds.postfinance.file']
        for d in directories:
            dir_name = d.name

            with sftp.cd(dir_name):
                list_name_files = sftp.listdir()
            sftp.get_d(dir_name, tmp_directory)
            _logger.info("[OK] download files in '%s' ", (dir_name))

            # Look for files to exclude
            excluded = d.excluded_files.split(';')
            for nameFile in list_name_files:
                file_ignore = [f for f in excluded if f and f in nameFile]
                if file_ignore:
                    self.msg_import_file_ignore += "; ".join(file_ignore)
                    continue

                # check if file exist already
                if fds_files_ids.search([['filename', '=', nameFile]]):
                    self.msg_exist_file += nameFile + "; "
                    _logger.warning("[FAIL] file '%s' already exist",
                                    (nameFile))
                    continue

                # save in the model fds_postfinance_files
                path = os.path.join(tmp_directory, nameFile)
                with open(path, "rb") as f:
                    file_data = f.read()
                values = {
                    'fds_account_id': fds_id.id,
                    'data': base64.b64encode(file_data),
                    'filename': nameFile,
                    'directory_id': d.id}
                fds_files_ids += fds_files_ids.create(values)

        return fds_files_ids

    @api.multi
    def _import2bankStatements(self, fds_files_ids):
        ''' private function that import the files to bank statments

            :param recordset: of model fds_postfinance_file
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
        # check key of active user
        fds_authentication_key_obj = self.env['fds.authentication.keys']
        key = fds_authentication_key_obj.search([
            ['user_id', '=', self.env.uid],
            ['fds_account_id', '=', self.fds_account_id.id]])

        # get username, hostname, key_pass
        hostname = self.fds_account_id.hostname
        username = self.fds_account_id.username
        key_pass = fds_authentication_key_obj.config()

        return (self.fds_account_id, hostname, username, key, key_pass)

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
