# -*- coding: utf-8 -*-
# © 2017 Compassion CH <http://www.compassion.ch>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import mock

from openerp.exceptions import Warning as UserError
from openerp.tests.common import TransactionCase

auth_keys = 'openerp.addons.l10n_ch_fds_postfinance.models' \
    '.fds_authentication_keys.FdsAuthenticationKeys'


class TestFds(TransactionCase):
    def setUp(self):
        super(TestFds, self).setUp()
        self.fds_account = self.env['fds.postfinance.account'].create({
            'name': 'FDS Test Account',
            'hostname': 'fdsbc.post.ch',
            'username': 'test-fds',
            'postfinance_email': 'fds@post.ch',
            'user_id': 1,
        })

    @mock.patch(auth_keys)
    def test_new_key(self, mock_keys):
        """
        Test generation of an authentication key-pair
        """
        # Mock the config to return a test password
        mock_keys.config.return_value = "Password"
        key_wizard = self.env['fds.key.generator.wizard'].with_context(
            active_ids=self.fds_account.ids, active_id=self.fds_account.id,
            active_model=self.fds_account._name
        ).create({'user_id': 1, 'state': 'default'})
        action = key_wizard.generate_keys_button()
        self.assertIsInstance(action, dict)
        self.assertIsNotNone(key_wizard.public_key)
        self.assertIsNotNone(key_wizard.private_key_crypted)
        self._valid_key_generation(action, key_wizard)
        key_wizard.confirm_keys_button()
        self.assertEqual(key_wizard.state, 'done')

        # Test we cannot generate several key-pairs
        key_wizard.state = 'default'
        with self.assertRaises(UserError):
            key_wizard.generate_keys_button()

    def test_import_keys(self):
        key_wizard = self.env['fds.key.import.wizard'].with_context(
            active_ids=self.fds_account.ids, active_id=self.fds_account.id,
            active_model=self.fds_account._name
        ).create({
            'user_id': 1,
            'public_key_import_txt': 'Foo',
            'private_key_import_txt': 'Bar',
            'state': 'default'
        })
        # Test wrong RSA key format
        with self.assertRaises(ValueError):
            key_wizard.import_keys_button()
        # Use a valid key-pair
        public, private = self.env[
            'fds.authentication.keys'].generate_pairkey()
        key_wizard.write({
            'public_key_import_txt': public,
            'private_key_import_txt': private,
        })
        action = key_wizard.import_keys_button()
        self._valid_key_generation(action, key_wizard)
        # Test we cannot import several key-pairs
        key_wizard.state = 'default'
        with self.assertRaises(UserError):
            key_wizard.import_keys_button()

    @mock.patch(auth_keys)
    def test_clone_keys(self, mock_keys):
        """ Test we can clone keys for different users. """
        # Mock the config to return a test password
        mock_keys.config.return_value = "Password"
        key_wizard = self.env['fds.key.generator.wizard'].with_context(
            active_ids=self.fds_account.ids, active_id=self.fds_account.id,
            active_model=self.fds_account._name
        ).create({'user_id': 1})
        key_wizard.generate_keys_button()
        src_key = key_wizard.fds_authentication_keys_id
        clone_wizard = self.env['fds.key.clone.wizard'].with_context(
            active_ids=self.fds_account.ids, active_id=self.fds_account.id,
            active_model=self.fds_account._name
        ).create({
            'src_user_key_id': src_key.id,
            'des_user_id': 4,
        })
        clone_wizard.copy_button()
        keys = self.fds_account.authentication_key_ids
        self.assertEqual(len(keys), 2)
        self.assertEqual(keys[0].public_key, keys[1].public_key)

    def _valid_key_generation(self, action, key_wizard):
        """Tests that keys are generated."""
        self.assertIsInstance(action, dict)
        fds_keys = self.fds_account.authentication_key_ids
        self.assertEqual(len(fds_keys), 1)
        self.assertEqual(key_wizard.public_key, fds_keys.public_key)
        self.assertEqual(key_wizard.state, 'generate')
