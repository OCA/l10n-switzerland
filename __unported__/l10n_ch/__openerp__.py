# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi. Copyright Camptocamp SA
#    Financial contributors: Hasa SA, Open Net SA,
#                            Prisme Solutions Informatique SA, Quod SA
#
#    Translation contributors: brain-tec AG, Agile Business Group
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

{'name': 'Switzerland - Accounting',
 'summary': 'Multilang swiss STERCHI account chart and taxes',
 'description': """
Swiss localization
==================

**Multilang swiss STERCHI account chart and taxes**
This localisation module creates the VAT taxes for sales and purchases
needed in Switzerland and provides the recommanded STERCHI chart of account
in french, italian and german.

**Related modules you may found interesting using OpenERP in Switzerland**

Various other modules have been made to work with OpenERP in Switzerland,
you may found some of them useful for you. Here is a list of the main ones:

 - **l10n_ch_bank**: List of swiss banks
 - **l10n_ch_zip**: List of swiss postal (ZIP)
 - **l10n_ch_dta**: Support of bank electronic payment (DTA)
 - **l10n_ch_sepa**: Support of SEPA/PAIN electronic payment
 - **l10n_ch_payment_slip**: Support of ESR/BVR payment slip report,
                             Reconciliation,
                             Report refactored with easy element positioning.
 - **l10n_ch_scan_bvr**: Scan the ESR/BVR reference to automatically create
                         the proper suplier invoice

All the modules are available on OpenERP swiss localization project on Github:
https://github.com/OCA/l10n-switzerland

You can also find them on apps.odoo.com.

**Author:** Camptocamp

**Financial contributors:** Prisme Solutions Informatique SA, Quod SA

**Translation contributors:** Brain-tec AG, Agile Business Group

""",
 'version': '7.1',
 'author': "Camptocamp,Odoo Community Association (OCA)",
 'category': 'Localization/Account Charts',
 'website': 'http://www.camptocamp.com',
 'license': 'AGPL-3',
 'depends': ['account', 'l10n_multilang'],
 'data': ['sterchi_chart/account.xml',
          'sterchi_chart/vat2011.xml',
          'sterchi_chart/fiscal_position.xml'],
 'demo': [],
 'test': [],
 'auto_install': False,
 'installable': True,
 'images': ['images/config_chart_l10n_ch.jpeg',
            'images/l10n_ch_chart.jpeg']
 }
