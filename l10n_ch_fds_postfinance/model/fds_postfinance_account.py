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

_logger = logging.getLogger(__name__)


class fds_postfinance_account(models.Model):
    ''' the FDS PostFinance configuration that allow to connect to the
        PostFinance server
    '''
    _name = 'fds.postfinance.account'

    name = fields.Char(
        string='Name',
        required=True,
        help='name'
    )
    hostname = fields.Char(
        string='Hostname SFTP Server',
        default='fds.post.ch',
        required=True,
        help='hostname of your sftp'
    )
    postfinance_mail = fields.Char(
        string='Mail PostFinance',
        default='fds@post.ch',
        required=True,
        help='mail of fds postfinance'
    )
    username = fields.Char(
        string='Username SFTP Server',
        required=True,
        help='username of your sftp account'
    )
    company_contact_id = fields.Many2one(
        comodel_name='res.users',
        string='Company Contact',
        ondelete='restrict',
        required=True,
        help='user that have create/contact with the fds postfinance account' +
             ', it will be use to send the public key to postfinance'
    )
    fds_authentication_keys_ids = fields.One2many(
        comodel_name='fds.authentication.keys',
        inverse_name='fds_account_id',
        string='fds authentication key in this account',
        help='user key for sftp connection'
    )
    fds_postfinance_files_ids = fields.One2many(
        comodel_name='fds.postfinance.files',
        inverse_name='fds_account_id',
        string='fds postfinance content',
        readonly=True,
        help='downloaded file from sftp'
    )
    fds_PF_files_directory_ids = fields.One2many(
        comodel_name='fds.postfinance.files.directory',
        inverse_name='fds_account_id',
        string='fds postfinance files directory',
        help='directory name of sftp FDS postfinnace'
    )

    ##################################
    #         Button action          #
    ##################################
    @api.multi
    def verifyDirectories_button(self):
        ''' test connection and verify if directories are the same in the DB

            :returns None:
            :raises Warning:
                - if current user do not have key
                - if unable to connect to sftp
        '''
        self.ensure_one()

        key = [e for e in self.fds_authentication_keys_ids
               if e.user_id == self.env.user]

        if not key:
            raise exceptions.Warning('You don\'t have key')

        if not key[0].active_key:
            raise exceptions.Warning('Key not active')

        try:
            (tmp_key, tmp_d) = self._create_tmp_file(
                key[0].private_key_crypted)
            key_pass = self.fds_authentication_keys_ids.config()

            # connect sftp
            with pysftp.Connection(self.hostname,
                                   username=self.username,
                                   private_key=tmp_key.name,
                                   private_key_pass=key_pass) as sftp:

                directories = sftp.listdir()

            # save new directories
            self._save_directories(directories)

        except Exception as e:
            _logger.error("Unable to connect to the sftp: %s", e)
            raise exceptions.Warning('Unable to connect to the sftp')

        finally:
            try:
                tmp_key.close()
            except:
                _logger.error("remove tmp_key file failed")
            try:
                shutil.rmtree(tmp_d)
            except:
                _logger.error("remove tmp directory failed")

    @api.multi
    def copyKey_button(self):
        ''' copy an authentication key to another user.

            :returns action: popup fds key clone wizard
        '''
        action = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'fds.key.clone.wizard',
            'target': 'new',
        }
        return action

    @api.multi
    def newKey_button(self):
        ''' generate a new authentication key to a user.

            :returns action: popup fds key generator wizard
        '''
        action = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'fds.key.generator.wizard',
            'target': 'new',
        }
        return action

    @api.multi
    def importKey_button(self):
        ''' import an authentication key to a user.

            :returns action: popup fds key import wizard
        '''
        action = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'fds.key.import.wizard',
            'target': 'new',
        }
        return action

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
    def _save_directories(self, directories):
        ''' private function that save the name of directory in db

            :returns None:
        '''
        dir_exist = [e.name for e in self.fds_PF_files_directory_ids]

        # add new directory
        directory_to_add = [dir for dir in directories if dir not in dir_exist]
        for dir in directory_to_add:
            values = {'name': dir, 'fds_account_id': self.id}
            self.fds_PF_files_directory_ids.create(values)
            _logger.info("[OK] add directory '%s' ", (dir))

        # change status if directory doesn't exist any more on the fds server
        dir_to_change = [dir for dir in dir_exist if dir not in directories]
        for dir in dir_to_change:
            fds_directory_ids = self.fds_PF_files_directory_ids.search([
                ['fds_account_id', '=', self.id],
                ['name', '=', dir]])
            fds_directory_ids.write({
                'still_on_server': False,
                'allow_download_file': False,
                'allow_upload_file': False})
            _logger.info("[OK] disable directory '%s' ", (dir))

        # check if 'still_on_server' correct
        dir_check = [e.name for e in self.fds_PF_files_directory_ids
                     if e.still_on_server is False and e.name in directories]
        for dir in dir_check:
            fds_directory_ids = self.fds_PF_files_directory_ids.search([
                ['fds_account_id', '=', self.id],
                ['name', '=', dir]])
            fds_directory_ids.write({'still_on_server': True})
