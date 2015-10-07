##############################################################################
#
#    Swiss localization Direct Debit module for OpenERP
#    Copyright (C) 2015 Compassion (http://www.compassion.ch)
#    @author: Emanuel Cino <ecino@compassion.ch>
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
from datetime import datetime, timedelta
from openerp import fields, exceptions, _
from openerp.tools import mod10r


def complete_line(nb_char, line=''):
    ''' In LSV/DD files each field has a defined length.
        This way, lines have to be filled with spaces (or truncated).
    '''
    if len(line) > nb_char:
        return line[:nb_char]

    return line.ljust(nb_char)


def get_treatment_date(prefered_type, line_mat_date, order_sched_date, name,
                       format='%Y%m%d'):
    ''' Returns appropriate date according to payment_order and
        payment_order_line data.
        Raises an error if treatment date is > today+30 or < today-10
    '''
    today = datetime.today()
    if prefered_type == 'due':
        requested_date = fields.Datetime.from_string(line_mat_date) \
            or today
    elif prefered_type == 'fixed':
        requested_date = fields.Datetime.from_string(order_sched_date) \
            or today
    elif prefered_type == 'now':
        requested_date = today
    else:
        raise exceptions.Warning('Preferred type not implemented')

    # Accepted dates are in range -90 to +90 days. We could go up
    # to +1 year, but we should be sure that we have less than
    # 1000 lines in payment order
    if requested_date > today + timedelta(days=90) \
            or requested_date < today - timedelta(days=90):
        raise exceptions.ValidationError(
            _('Incorrect treatment date: %s for line with '
              'ref %s') % (requested_date, name)
        )

    return requested_date.strftime(format)


def is_bvr_ref(ref):
    if not ref:
        return False  # Empty is not valid
    clean_ref = ref.replace(' ', '')
    if not clean_ref.isdigit() or len(clean_ref) > 27:
        return False
    clean_ref = clean_ref.rjust(27, '0')  # Add zeros to the left
    if not clean_ref == mod10r(clean_ref[0:26]):
        return False

    return True


def check_currency(line, properties):
    ''' Check that line currency is equal to dd export currency '''
    if not line.currency.name == properties.get('currency'):
        raise exceptions.ValidationError(
            _('Line with ref %s has %s currency and generated '
              'file %s (should be the same)') %
            (line.name, line.currency.name, properties.get(
                'currency', ''))
        )
