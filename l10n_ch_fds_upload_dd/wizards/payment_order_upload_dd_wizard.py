# -*- coding: utf-8 -*-
##############################################################################
#
#    Swiss Postfinance File Delivery Services module for Odoo
#    Copyright (C) 2014-2016 Compassion CH
#    @author: Nicolas Tran, Emanuel Cino
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
import base64
import logging
import os
from tempfile import mkstemp

import openerp
from openerp import models, fields, api, exceptions, _

try:
    import pysftp
except ImportError:
    raise ImportError(
        'This module needs pysftp to connect to the FDS. '
        'Please install pysftp on your system. (sudo pip install pysftp)'
    )

_logger = logging.getLogger(__name__)


class PaymentOrderUploadDD(models.TransientModel):
    """ This addon allows you to upload the Direct Debit generated file to
        your FDS Postfinance.
    """
    _name = 'payment.order.upload.dd.wizard'
    _description = 'Upload DD to FDS'

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
    attachment_id = fields.Many2one(
        'ir.attachment', required=True, ondelete='cascade'
    )
    file_data = fields.Binary(
        'Generated File', related='attachment_id.datas', readonly=True
    )
    filename = fields.Char(
        related='attachment_id.name', readonly=True
    )
    payment_order_id = fields.Many2one(
        'account.payment.order', 'Payment Order', required=True, readonly=True,
        ondelete='cascade'
    )
    state = fields.Selection(
        selection=[
            ('upload', 'upload'),
            ('finish', 'finish')],
        readonly=True,
        default='upload',
    )

    ##################################
    #         Button action          #
    ##################################
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

        # check key of active user
        fds_keys_obj = self.env['fds.authentication.keys']
        key = fds_keys_obj.search([
            ['user_id', '=', self.env.uid],
            ['fds_account_id', '=', self.fds_account_id.id],
            ['key_active', '=', True]])

        if not key:
            raise exceptions.Warning(
                _("You don't have access to the selected FDS account."))

        # create tmp file
        key_fd, key_file = mkstemp()
        data_fd, data_file = mkstemp()
        try:
            os.write(key_fd, base64.b64decode(key.private_key_crypted))
            os.write(data_fd, base64.b64decode(self.attachment_id.datas))
        finally:
            os.close(key_fd)
            os.close(data_fd)
        key_pass = fds_keys_obj.config()

        # upload to sftp
        with pysftp.Connection(self.fds_account_id.hostname,
                               username=self.fds_account_id.username,
                               private_key=key_file,
                               private_key_pass=key_pass) as sftp:
            with sftp.cd(self.fds_directory_id.name):
                # Here we want to commit to make sure we see
                # the file was uploaded and avoid sending it again.
                with api.Environment.manage():
                    with openerp.registry(
                            self.env.cr.dbname).cursor() as new_cr:
                        new_env = api.Environment(
                            new_cr, self.env.uid, self.env.context)
                        wizard = self.with_env(new_env)
                        sftp.put(data_file,
                                 remotepath=self.attachment_id.name.replace(
                                     '/', '-'))
                        wizard.state = 'finish'
                        _logger.info("[OK] upload file (%s) ", wizard.filename)

        self._add2historical()

        os.remove(key_file)
        os.remove(data_file)

        self.payment_order_id.generated2uploaded()
        return True

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
    def _add2historical(self):
        ''' private function that add the upload file to historic

            :returns: None
        '''
        self.ensure_one()
        values = {
            'payment_order_id': self.payment_order_id.id,
            'fds_account_id': self.fds_account_id.id,
            'filename': self.filename,
            'directory_id': self.fds_directory_id.id,
            'state': 'uploaded'}
        historical_dd_obj = self.env['fds.postfinance.historical.dd']
        historical_dd_obj.create(values)
