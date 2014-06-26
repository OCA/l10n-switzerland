# -*- coding: utf-8 -*-
##############################################################################
#
#    Author Vincent Renaville. Copyright 2013 Camptocamp SA
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
"name" : "Switzerland - Credit control with ESR/BVR",
"summary": "Print ESR/BVR for credit control",
"description" : """
Swiss Credit control using ESR/BVR
==================================

This addon adds the possibility to print ESR/BVR of related credit control
lines. He is useful if you use the credit control module (account_credit_control). 
This module allow you to manage advance credit controlling and is hosted here :
https://launchpad.net/account-financial-tools

You can also find this module on apps.openerp.com

""",
"version" : "1.0",
"author" : "Camptocamp",
"category" : "Generic Modules/Others",
"website": "http://www.camptocamp.com",
"depends" : [
                "account_credit_control",
                "l10n_ch_payment_slip"
            ],
"data" :[
                    "credit_control_printer_view.xml",
                    "report.xml"
                ],
"active": False,
"installable": True
}
