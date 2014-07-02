# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi, Vincent Renaville
#    Copyright 2012 Camptocamp SA
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

{"name": "Wizard to Scan BVR for Invoice",
 "description": """
create invoices from BVR code

This module works with C-channel or other OCR scanner.

It helps you to create an invoice directly from the BVR Code. Find the menu entry
called "Scan BVR" under Accounting -> Supplier. It open a popup from which you
can scan the BVR number. It'll recognize the needed information and create an 
invoice for the right supplier.

If you have completed the field "Default product supplier invoice" on the concerned
supplier, it'll create a line with the proper amount and the given product.

It currently supports BVR and BVR+

""",
 "version": "1.0",
 "author": "Camptocamp",
 "category": "Generic Modules/Others",
 "website": "http://www.camptocamp.com",
 "depends": ["l10n_ch",
             "l10n_ch_payment_slip"],
 "data": ["wizard/scan_bvr_view.xml",
          "partner_view.xml",
          "bank_view.xml"],
 "installable": True
 }
