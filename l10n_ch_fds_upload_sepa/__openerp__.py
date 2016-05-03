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
{
    'name': 'Swiss Postfinance FDS SEPA upload',
    'summary': "Upload SEPA files to FDS PostFinance",
    'version': '8.0.1.0.1',
    'license': 'AGPL-3',
    'author': 'Compassion CH, Odoo Comunity Association (OCA)',
    'website': 'http://www.compassion.ch/',
    'category': 'Finance',
    'depends': [
        'l10n_ch_fds_postfinance',
        'l10n_ch_sepa',
    ],
    'external_dependencies': {
        'python': ['pysftp']
    },
    'data': [
        'views/fds_inherit_sepa_wizard_view.xml',
        'views/fds_postfinance_account_sepa_view.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}
