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
{
    'name': 'Swiss Postfinance File Delivery Services',
    'summary': 'Download files and import bank statements from FDS',
    'version': '11.0.1.0.2',
    'license': 'AGPL-3',
    'author': 'Compassion CH, Odoo Community Association (OCA)',
    'website': 'http://www.compassion.ch/',
    'category': 'Finance',
    'depends': ['account'],
    'external_dependencies': {
        'python': ['pysftp', 'Crypto']
    },
    'data': [
        'data/import_files_cron.xml',
        'views/fds_authentication_keys_view.xml',
        'views/fds_files_import_tobankstatments_wizard_view.xml',
        'views/fds_key_clone_wizard_view.xml',
        'views/fds_key_generator_wizard_view.xml',
        'views/fds_key_import_wizard_view.xml',
        'views/fds_postfinance_account_view.xml',
        'views/fds_postfinance_file_view.xml',
        'security/ir.model.access.csv',
    ],
    'images': [],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
