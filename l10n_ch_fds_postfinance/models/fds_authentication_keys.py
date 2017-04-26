# -*- coding: utf-8 -*-
# © 2015 Compassion CH (Nicolas Tran)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging
from openerp import models, fields, api
from openerp.tools.config import config

logger = logging.getLogger(__name__)

try:
    from Crypto.PublicKey import RSA
    from Crypto import Random
except ImportError:
    logger.debug(
        'This module needs Crypto to generate SSH keys. '
        'Please install pycrypto on your system. (sudo pip install pycrypto)'
    )


class FdsAuthenticationKeys(models.Model):
    ''' this class generate RSA key pair with the private key crypted and
        store the key in the database
    '''
    _name = 'fds.authentication.keys'
    _rec_name = 'user_id'

    user_id = fields.Many2one(
        comodel_name='res.users',
        string='User',
        ondelete='restrict',
        readonly=True,
    )
    fds_account_id = fields.Many2one(
        comodel_name='fds.postfinance.account',
        string='FDS account',
        ondelete='restrict',
        readonly=True,
    )
    public_key = fields.Binary(
        readonly=True,
    )
    private_key_crypted = fields.Binary(
        string='Private key crypted',
        readonly=True,
    )
    pub_filename = fields.Char(
        string='Public key filename',
        readonly=True,
    )
    ppk_filename = fields.Char(
        string='Private key filename',
        readonly=True,
    )
    key_active = fields.Boolean(
        default=True,
    )

    @api.multi
    def config(self):
        ''' Configuration RSA: password to encrypt the private key.
            Note: the password must be add in the odoo config file
            (ie. ssh_pwd = *****)

            :returns str: the pass key that allow to decrypt the private key
        '''
        password = config.get('ssh_pwd')
        return password

    @api.multi
    def generate_pairkey(self, bits=4096):
        ''' generate the RSA key pair.

            :returns (str, str): public key and private key crypted
        '''
        generator = Random.new().read
        keys = RSA.generate(bits, generator)
        private_key_crypted = keys.exportKey("PEM", self.config())
        public_key = keys.publickey().exportKey("OpenSSH")

        return (public_key, private_key_crypted)

    @api.multi
    def import_pairkey(self, public_key, private_key):
        ''' import and crypte private key.

            :returns (str, str): public key and private key crypted
        '''
        importKey = RSA.importKey(private_key)
        private_key_crypted = importKey.exportKey("PEM", self.config())

        return (public_key, private_key_crypted)

    @api.multi
    def clone_key_to(self, user):
        ''' create a new record with the same key

            :params record: of model res.users
            :return record: of model fds.authentication.key
        '''
        values = {
            'user_id': user.id,
            'fds_account_id': self.fds_account_id.id,
            'public_key': self.public_key,
            'private_key_crypted': self.private_key_crypted,
            'pub_filename': self.pub_filename,
            'ppk_filename': self.ppk_filename,
            'key_active': self.key_active}

        return self.create(values)
