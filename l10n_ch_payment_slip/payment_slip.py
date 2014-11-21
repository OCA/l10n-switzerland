# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Nicolas Bessi
#    Copyright 2014 Camptocamp SA
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
import StringIO
import contextlib
import re
from PIL import Image, ImageDraw, ImageFont

from openerp import models, fields, api, _
from openerp.modules import get_module_resource
from openerp import exceptions
from openerp.tools.misc import mod10r


class PaymentSlip(models.Model):
    """From Version 8 payment slip are now a
    new Model related to move line and
    stored in database. This is done because
    with previous implementation changing bank data
    or anything else had as result to modify historical refs.

    Now payment slip is genrated each time a customer invoice is validated
    If you need to alter a payment slip you will have to cancel
    and revalidate the related invoice
    """
    _fill_color = (0, 0, 0, 255)
    _default_font_size = 20
    _default_scan_font_size = 22
    _default_amount_font_size = 30
    _compile_get_ref = re.compile('[^0-9]')
    _compile_check_bvr = re.compile('[0-9][0-9]-[0-9]{3,6}-[0-9]')

    _name = 'l10n_ch.payment_slip'
    _rec_name = 'reference'

    reference = fields.Char('BVR/ESR Ref.',
                            compute='compute_ref',
                            store=True)

    move_line_id = fields.Many2one('account.move.line',
                                   string='Related move',
                                   readonly=True,
                                   ondelete='cascade')

    amount_total = fields.Float('Total amount of BVR/ESR',
                                compute='compute_amount',
                                store=True)

    scan_line = fields.Char('Scan Line',
                            compute='compute_scan_line',
                            readonly=True,
                            store=True)

    invoice_id = fields.Many2one(string='Related invoice',
                                 related='move_line_id.invoice',
                                 store=True,
                                 readonly=True,
                                 comodel_name='account.invoice')

    slip_image = fields.Binary('Slip Image',
                               readonly=True,
                               compute="draw_payment_slip_image")

    a4_pdf = fields.Binary('Slip A4 PDF',
                           readonly=True,
                           compute="draw_a4_report")

    _sql_constraints = [('unique reference',
                         'UNIQUE (reference)',
                        'BVR/ESR reference must be unique')]

    @api.model
    def _can_generate(self, move_line):
        '''Predicate to determine if payment slip should be generated or not.

        :param move_line: move line reocord
        :type move_line: :py:class:`openerp.models.Model` record

        :return: True if we can generate a payment slip
        :rtype: bool
        '''
        invoice = move_line.invoice
        if not invoice:
            return False
        return (invoice.partner_bank_id and
                invoice.partner_bank_id.state == 'bvr')

    def _get_adherent_number(self):
        self.ensure_one()
        move_line = self.move_line_id
        ad_number = ''
        if move_line.invoice.partner_bank_id.bvr_adherent_num:
            ad_number = move_line.invoice.partner_bank_id.bvr_adherent_num
        return ad_number

    def _compute_amount_hook(self):
        """Hook to return the total amount of pyament slip

        :return: total amount of payment slip
        :rtype: float

        """
        self.ensure_one()
        return self.move_line_id.debit

    @api.one
    @api.depends('move_line_id',
                 'move_line_id.debit',
                 'move_line_id.credit')
    def compute_amount(self):
        """Return the total amount of pyament slip

        if you need to override please use
        :py:meth:`_compute_amount_hook`

        :return: total amount of payment slip
        :rtype: float

        """
        amt = self._compute_amount_hook()
        self.amount_total = amt
        return amt

    @api.one
    @api.depends('move_line_id')
    def compute_ref(self):
        """Retrieve ESR/BVR reference from move line in order to print it

        Returns False when no BVR reference should be generated.  No
        reference is generated when a transaction reference already
        exists for the line (likely been generated by a payment service).
        """
        if not self._can_generate(self.move_line_id):
            return ''
        move_line = self.move_line_id
        # We sould not use technical id but will keep it for historical reason
        move_number = str(move_line.id)
        ad_number = self._get_adherent_number()
        if move_line.invoice.number:
            compound = move_line.invoice.number + str(move_line.id)
            move_number = self._compile_get_ref.sub('', compound)
        reference = mod10r(
            ad_number + move_number.rjust(26 - len(ad_number), '0')
        )
        self.reference = self._space(reference)
        return reference

    @api.model
    def _space(self, nbr, nbrspc=5):
        """Spaces ref by group of 5 digits.

        Example:
            AccountInvoice._space('123456789012345')
            '12 34567 89012 345'

        :param nbr: reference to group
        :type nbr: int

        :param nbrspc: group length
        :type nbrspc: int

        :return: grouped reference
        :rtype: str

        """
        return ''.join([' '[(i - 2) % nbrspc:] + c for i, c in enumerate(nbr)])

    def _compute_scan_line_list(self):
        """Generate a list containing all element of scan line

        the element are grouped by char or symbol

        This will allows the free placment of each element
        and enable a fine tuning of spacing

        :return: a list of sting representing the scan bar

        :rtype: list
        """
        self.ensure_one()
        line = []
        if not self._can_generate(self.move_line_id):
            return []
        amount = '01%.2f' % self.amount_total
        justified_amount = amount.replace('.', '').rjust(10, '0')
        line += [char for char in mod10r(justified_amount)]
        line.append('>')
        line += [char for char in self.compute_ref()[0]]
        line.append('+')
        line.append(' ')
        bank = self.move_line_id.invoice.partner_bank_id.get_account_number()
        account_components = bank.split('-')
        bank_identifier = "%s%s%s" % (
            account_components[0],
            account_components[1].rjust(6, '0'),
            account_components[2]
        )
        line += [car for car in bank_identifier]
        line.append('>')
        return line

    @api.one
    @api.depends('move_line_id',
                 'move_line_id.debit',
                 'move_line_id.credit')
    def compute_scan_line(self):
        """Compute the payment slip scan line to be used
        by scanners

        :return: scan line
        :rtype: str
        """
        scan_line_list = self._compute_scan_line_list()
        self.scan_line = ''.join(scan_line_list)

    @api.model
    def get_slip_for_move_line(self, move_line):
        """Return pyment slip related to move

        :param move: `account.move.line` record
        :type move: :py:class:`openerp.models.Model`

        :return: payment slip recordset related to move line
        :rtype: :py:class:`openerp.models.Model`
        """
        return self.search(
            [('move_line_id', '=', move_line.id)]
        )

    @api.model
    def create_slip_from_move_line(self, move_line):
        """Generate `l10n_ch.payment_slip` from
        `account.move.line` recordset

        :param move_lines: Record of `account.move.line`
        :type move_line: :py:class:`openerp.models.Model`

        :return: Recordset of `l10n_ch.payment_slip`
        :rtype: :py:class:`openerp.models.Model`
        """
        return self.create({'move_line_id': move_line.id})

    @api.model
    def compute_pay_slips_from_move_lines(self, move_lines):
        """Get or generate `l10n_ch.payment_slip` from
        `account.move.line` recordset

        :param move_lines: Recordset of `account.move.line`
        :type move_lines: :py:class:`openerp.models.Model`

        :return: Recordset of `l10n_ch.payment_slip`
        :rtype: :py:class:`openerp.models.Model`

        """
        pay_slips = self.browse()
        for move in move_lines:
            if not self._can_generate(move):
                continue
            slip = self.get_slip_for_move_line(move)
            if not slip:
                slip = self.create_slip_from_move_line(move)
            if slip:
                pay_slips += slip
        return pay_slips

    @api.model
    def compute_pay_slips_from_invoices(self, invoices):
        """Generate ```l10n_ch.payment_slip``` from
        ```account.invoice``` recordset

        :param move_lines: Recordset of `account.invoice`
        :type move_lines: :py:class:`openerp.models.Model`

        """
        move_lines = self.env['account.move.line'].browse()
        for invoice in invoices:
            move_lines += invoice.get_payment_move_line()
        return self.compute_pay_slips_from_move_lines(move_lines)

    def get_comm_partner(self):
        self.ensure_one()
        invoice = self.move_line_id.invoice
        if hasattr(invoice, 'commercial_partner_id'):
            return invoice.commercial_partner_id
        else:
            return invoice.partner_id

    @api.one
    def _validate(self):
        """Check if the payment slip is ready to be printed"""
        invoice = self.move_line_id.invoice
        if not invoice:
            raise exceptions.ValidationError(
                _('No invoice related to move line %') % self.move_line_id.ref
            )
        if not self._compile_check_bvr.match(
                invoice.partner_bank_id.get_account_number() or ''):
            raise exceptions.ValidationError(
                _('Your bank BVR number should be of the form 0X-XXX-X! '
                  'Please check your company '
                  'information for the invoice:\n%s') % (invoice.name)
            )
        return True

    @api.model
    def police_absolute_path(self):
        """Will get the ocrb police absolute path"""
        path = get_module_resource('l10n_ch_payment_slip',
                                   'static',
                                   'src',
                                   'font',
                                   'ocrbb.ttf')
        return path

    @api.model
    def image_absolute_path(self, file_name):
        """Will get the ocrb police absolute path"""
        path = get_module_resource('l10n_ch_payment_slip',
                                   'static',
                                   'src',
                                   'img',
                                   file_name)
        return path

    @api.model
    def _get_text_font(self):
        return ImageFont.truetype(self.police_absolute_path(),
                                  self._default_font_size)

    @api.model
    def _get_amount_font(self):
        return ImageFont.truetype(self.police_absolute_path(),
                                  self._default_amount_font_size)

    @api.model
    def _get_scan_line_text_font(self, company):
        return ImageFont.truetype(
            self.police_absolute_path(),
            company.bvr_scan_line_font_size or self._default_scan_font_size
        )

    @api.model
    def _draw_address(self, draw, font, com_partner, initial_position,
                      company):
        x, y = initial_position
        x += company.bvr_add_horz
        y += company.bvr_add_vert
        draw.text((x, y), com_partner.name, font=font, fill=self._fill_color)
        y += self._default_font_size
        for line in com_partner.contact_address.split("\n"):
            if not line:
                continue
            width, height = font.getsize(line)
            draw.text((x, y),
                      line,
                      font=font,
                      fill=self._fill_color)
            y += self._default_font_size

    @api.model
    def _draw_bank(self, draw, font, bank, initial_position, company):
        x, y = initial_position
        x += company.bvr_delta_horz
        y += company.bvr_delta_vert
        draw.text((x, y), bank, font=font, fill=self._fill_color)

    @api.model
    def _draw_ref(self, draw, font, ref, initial_position, company):
        x, y = initial_position
        x += company.bvr_delta_horz
        y += company.bvr_delta_vert
        draw.text((x, y), ref, font=font, fill=self._fill_color)

    @api.model
    def _draw_amont(self, draw, font, amount, initial_position, company):
        x, y = initial_position
        x += company.bvr_delta_horz
        y += company.bvr_delta_vert
        indice = 0
        for car in amount[::-1]:
            width, height = font.getsize(car)
            if indice:
                # some font type return non numerical
                x -= float(width) / 2.0
            draw.text((x, y), car, font=font, fill=self._fill_color)
            x -= 11 + float(width) / 2.0
            indice += 1

    @api.model
    def _draw_scan_line(self, draw, font, initial_position, company):
        x, y = initial_position
        x += company.bvr_scan_line_horz
        y += company.bvr_scan_line_vert
        indice = 0
        for car in self._compute_scan_line_list()[::-1]:
            width, height = font.getsize(car)
            if indice:
                # some font type return non numerical
                x -= float(width) / 2.0
            draw.text((x, y), car, font=font, fill=self._fill_color)
            x -= 1.4 + float(width) / 2.0
            indice += 1

    @api.model
    def _draw_hook(self, draw):
        pass

    def _draw_payment_slip(self, a4=False, out_format='PNG', scale=None,
                           b64=False):
        """Generate the payment slip image"""
        a4_offset = 0.0
        if a4:
            a4_offset = 1083
        self.ensure_one()
        company = self.env.user.company_id
        default_font = self._get_text_font()
        amount_font = self._get_amount_font()
        invoice = self.move_line_id.invoice
        scan_font = self._get_scan_line_text_font(company)
        bank_acc = self.move_line_id.invoice.partner_bank_id
        if company.bvr_background:
            if a4:
                base_image_path = self.image_absolute_path('a4bvr.png')
            else:
                base_image_path = self.image_absolute_path('bvr.png')
        else:
            if a4:
                base_image_path = self.image_absolute_path('a4.png')
            else:
                base_image_path = self.image_absolute_path('white.png')
        base = Image.open(base_image_path).convert('RGB')
        draw = ImageDraw.Draw(base)
        if invoice.partner_bank_id.print_partner:
            initial_position = (10, 45 + a4_offset)
            self._draw_address(draw, default_font, company.partner_id,
                               initial_position, company)
            initial_position = (355, 45 + a4_offset)
            self._draw_address(draw, default_font, company.partner_id,
                               initial_position, company)
        com_partner = self.get_comm_partner()
        initial_position = (10, 355 + a4_offset)
        self._draw_address(draw, default_font, com_partner,
                           initial_position, company)
        num_car, frac_car = ("%.2f" % self.amount_total).split('.')
        self._draw_amont(draw, amount_font, num_car,
                         (214, 290 + a4_offset), company)
        self._draw_amont(draw, amount_font, frac_car,
                         (306, 290 + a4_offset), company)
        self._draw_amont(draw, amount_font, num_car,
                         (560, 290 + a4_offset), company)
        self._draw_amont(draw, amount_font, frac_car,
                         (650, 290 + a4_offset), company)

        if invoice.partner_bank_id.print_account:
            self._draw_bank(draw, default_font,
                            bank_acc.get_account_number(),
                            (144, 245 + a4_offset), company)
            self._draw_bank(draw, default_font,
                            bank_acc.get_account_number(),
                            (490, 245 + a4_offset), company)

        self._draw_ref(draw, default_font, self.reference,
                       (745, 195 + a4_offset), company)
        self._draw_scan_line(draw, scan_font, (1140, 485 + a4_offset), company)
        self._draw_hook(draw)
        with contextlib.closing(StringIO.StringIO()) as buff:
            dpi = base.info['dpi']
            if scale:
                width, height = base.size
                base = base.resize((int(width*scale), int(height*scale)))
            if out_format == 'PDF':
                base.save(buff, out_format, dpi=dpi, resolution=dpi[0])
            else:
                base.save(buff, out_format, dpi=dpi)
            img_stream = buff.getvalue()
            if b64:
                img_stream = base64.encodestring(img_stream)
            return img_stream

    def draw_payment_slip_image(self):
        img = self._draw_payment_slip()
        self.slip_image = base64.encodestring(img)
        return img

    def draw_a4_report(self):
        img = self._draw_payment_slip(a4=True, out_format='PDF')
        self.a4_pdf = base64.encodestring(img)
        return img
