# -*- coding: utf-8 -*-
# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api, exceptions, _
import logging
import base64
import tempfile
import shutil


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


class FdsPostfinanceAccount(models.Model):
    """" the FDS PostFinance configuration that allow to connect to the
        PostFinance server
    """
    _name = 'fds.postfinance.account'

    name = fields.Char(
        required=True
    )
    hostname = fields.Char(
        string='SFTP Hostname',
        default='fdsbc.post.ch',
        required=True,
    )
    postfinance_email = fields.Char(
        default='fds@post.ch',
        required=True,
        help='E-mail of FDS Postfinance'
    )
    username = fields.Char(
        string='SFTP Username',
        required=True,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Account Owner',
        ondelete='restrict',
        required=True,
        help='Owner must have the rights to register new key pairs for this '
             'account. Its e-mail address will be used to send the keys '
             'of new users to PostFinance'
    )
    authentication_key_ids = fields.One2many(
        comodel_name='fds.authentication.keys',
        inverse_name='fds_account_id',
        string='Authentication keys',
    )
    fds_file_ids = fields.One2many(
        comodel_name='fds.postfinance.file',
        inverse_name='fds_account_id',
        string='FDS Postfinance files',
        readonly=True,
        help='downloaded files from sftp'
    )
    directory_ids = fields.One2many(
        comodel_name='fds.postfinance.directory',
        inverse_name='fds_account_id',
        string='FDS postfinance directories',
    )

    ##################################
    #         Button action          #
    ##################################
    @api.multi
    def verify_directories_button(self):
        """ test connection and verify if directories are the same in the DB

            :returns None:
            :raises Warning:
                - if current user do not have key
                - if unable to connect to sftp
        """
        self.ensure_one()
        if not SFTP_OK:
            raise exceptions.Warning(
                _("Please install pysftp to use this feature."))

        key = [e for e in self.authentication_key_ids
               if e.user_id == self.env.user]

        if not key:
            raise exceptions.Warning(_("You don't have key"))

        if not key[0].key_active:
            raise exceptions.Warning(_('Key not active'))

        try:
            (tmp_key, tmp_d) = self._create_tmp_file(
                key[0].private_key_crypted)
            key_pass = self.authentication_key_ids.config()

            # connect sftp
            with pysftp.Connection(
                    self.hostname, username=self.username,
                    private_key=tmp_key.name, private_key_pass=key_pass
            ) as sftp:
                directories = sftp.listdir()

            # save new directories
            self._save_directories(directories)

        except Exception as e:
            _logger.error("Unable to connect to the sftp: %s", e)
            raise exceptions.Warning(_('Unable to connect to the sftp'))

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
    def copy_key_button(self):
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
    def import_key_button(self):
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

    @api.model
    def import_files_cron(self):
        """
        Import files for all Accounts defined.
        :return: True
        """
        accounts = self.search([])
        for account in accounts:
            self.env['fds.files.import.tobankstatments.wizard'].create({
                'fds_account_id': account.id,
                'state': 'default'
            }).import_button()
        return True

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
        dir_exist = self.directory_ids.mapped('name')

        # add new directory
        directory_to_add = [dir for dir in directories if dir not in dir_exist]
        for directory in directory_to_add:
            values = {'name': directory, 'fds_account_id': self.id}
            self.directory_ids.create(values)
            _logger.info("[OK] add directory '%s' ", (directory))

        # change status if directory doesn't exist any more on the fds server
        dir_to_change = [dir for dir in dir_exist if dir not in directories]
        for directory in dir_to_change:
            fds_directory_ids = self.directory_ids.search([
                ['fds_account_id', '=', self.id],
                ['name', '=', directory]])
            fds_directory_ids.write({
                'still_on_server': False,
                'allow_download_file': False,
                'allow_upload_file': False})
            _logger.info("[OK] disable directory '%s' ", (directory))

        # check if 'still_on_server' correct
        dir_check = [e.name for e in self.directory_ids
                     if e.still_on_server is False and e.name in directories]
        for directory in dir_check:
            fds_directory_ids = self.directory_ids.search([
                ['fds_account_id', '=', self.id],
                ['name', '=', directory]])
            fds_directory_ids.write({'still_on_server': True})
