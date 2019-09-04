# Copyright 2014-2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import io
import contextlib
import re
import textwrap
from collections import namedtuple
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from odoo import models, fields, api, _, exceptions, tools
from odoo.modules import get_module_resource
from odoo.tools.misc import mod10r, format_date

FontMeta = namedtuple('FontMeta', ('name', 'size'))


ADDR_FORMAT = "%(street)s\n%(street2)s\n%(zip)s %(city)s"
PARTNER_NUM_SIZE = 7


class PaymentSlipSettings(object):
    """Slip report setting container"""

    def __init__(self, report_name, **kwargs):
        for param, value in kwargs.items():
            setattr(self, param, value)
        self.report_name = report_name
        self.validate()

    def validate(self):
        "Parameter Validationd hook"""
        pass


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
    _fill_color = (0, 0, 0)
    _default_font_size = 11
    _default_scan_font_size = 11
    _default_amount_font_size = 16
    _compile_get_ref = re.compile(r'\D')

    _name = 'l10n_ch.payment_slip'
    _description = 'Payment Slip'
    _rec_name = 'reference'

    reference = fields.Char('ISR Ref.',
                            compute='_compute_ref',
                            index=True,
                            store=True)

    move_line_id = fields.Many2one('account.move.line',
                                   string='Related move',
                                   readonly=True,
                                   ondelete='cascade')

    amount_total = fields.Float('Total amount of ISR',
                                compute='_compute_amount')

    scan_line = fields.Char('Scan Line',
                            compute='_compute_scan_line',
                            readonly=True)

    invoice_id = fields.Many2one(string='Related invoice',
                                 related='move_line_id.invoice_id',
                                 store=True,
                                 readonly=True,
                                 comodel_name='account.invoice')

    slip_image = fields.Binary('Slip Image',
                               readonly=True,
                               compute="_compute_payment_slip_image")

    a4_pdf = fields.Binary('Slip A4 PDF',
                           readonly=True,
                           compute="_compute_a4_report")

    _sql_constraints = [('unique reference',
                         'UNIQUE (reference)',
                        'ISR reference must be unique')]

    @api.model
    def _can_generate(self, move_line):
        '''Predicate to determine if payment slip should be generated or not.

        :param move_line: move line reocord
        :type move_line: :py:class:`openerp.models.Model` record

        :return: True if we can generate a payment slip
        :rtype: bool
        '''
        invoice = move_line.invoice_id
        if not invoice:
            return False
        return invoice.partner_bank_id and invoice.l10n_ch_isr_subscription

    def _get_isr_subscription_number(self):
        """Fetch the current slip bank adherent number.

        :return: adherent number
        :rtype: string
        """
        self.ensure_one()
        move_line = self.move_line_id
        return move_line.invoice_id.l10n_ch_isr_subscription or ''

    def _get_isrb_id_number(self):
        self.ensure_one()
        partner_bank = self.move_line_id.invoice_id.partner_bank_id
        return partner_bank.l10n_ch_isrb_id_number or ''

    def _compute_amount_hook(self):
        """Hook to return the total amount of payment slip

        :return: total amount of payment slip
        :rtype: float
        """
        return self.move_line_id.debit

    @api.depends('move_line_id',
                 'move_line_id.debit',
                 'move_line_id.credit')
    def _compute_amount(self):
        """Return the total amount of payment slip

        If you need to override please use
        :py:meth:`_compute_amount_hook`

        :return: total amount of payment slip
        :rtype: float

        """
        for rec in self:
            amt = rec._compute_amount_hook()
            rec.amount_total = amt

    def _get_partner_number(self):
        move_line = self.move_line_id
        partner_ref = move_line.invoice_id.partner_id.ref or ''
        partner_number = self._compile_get_ref.sub('', partner_ref)
        if len(partner_number) > 7:
            extra = len(partner_number) - 7
            partner_number = partner_number[extra:]
        return partner_number.rjust(
            PARTNER_NUM_SIZE, '0'
        )

    @api.depends('move_line_id',
                 'move_line_id.invoice_id.number',
                 'move_line_id.invoice_id.partner_id.ref')
    def _compute_ref(self):
        # pylint: disable=anomalous-backslash-in-string
        """Retrieve ISR reference from move line in order to print it

        Returns False when no ISR reference should be generated.  No
        reference is generated when a transaction reference already
        exists for the line (likely been generated by a payment service).

        Reference can be a single move line and can optionnally contain
        ISR-B Customer ID number and a partner number to match with reference.

        110011215040203632940468930
        \_________/\_____/\______/|
             1        2       3   4

        (1) ISR-B Customer ID number (size: may vary)
        (2) Partner reference filled by 0 on the left (size: 7)
        (3) Invoice reference filled by 0 on the left (size: what is left)
        (4) Control digit (size: 1)
        """
        # pylint: enable=anomalous-backslash-in-string
        for rec in self:
            move_line = rec.move_line_id
            if not rec._can_generate(move_line):
                continue
            # We should not use technical id but will keep it for
            # historical reason
            move_number = str(move_line.id)
            id_number = rec._get_isrb_id_number()
            partner_number = rec._get_partner_number()
            if move_line.invoice_id.number:
                compound = move_line.invoice_id.number + str(move_line.id)
                move_number = rec._compile_get_ref.sub('', compound)
            # take only last digits of move if it exceed boundaries
            extra = len(move_number) + len(id_number) + PARTNER_NUM_SIZE - 26
            if extra > 0:
                move_number = move_number[extra:]
            move_number = move_number.rjust(
                26 - len(id_number) - PARTNER_NUM_SIZE, '0'
            )
            reference = mod10r(id_number + partner_number + move_number)
            rec.reference = rec._space(reference)

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
        justified_amount = '01%s' % ('%.2f' % self.amount_total).replace(
            '.', '').rjust(10, '0')
        line.extend(mod10r(justified_amount))
        line.append('>')
        line.extend(self.reference.replace(" ", ""))
        line.append('+')
        line.append(' ')
        invoice = self.move_line_id.invoice_id
        line.extend(invoice.l10n_ch_isr_subscription)
        line.append('>')
        return line

    @api.depends('amount_total',
                 'reference',
                 'move_line_id',
                 'move_line_id.debit',
                 'move_line_id.credit')
    def _compute_scan_line(self):
        # pylint: disable=anomalous-backslash-in-string
        """Compute the payment slip scan line to be used by scanners

        A scan line can have the 2 following formats:

        ISR (Postfinance)

        0100003949753> 120000000000234478943216899+ 010001628
        |/\________/|  \________________________/|  \_______/
        1     2     3           4                5      6

        (1) 01 | header constant
        (2) 0000394975 | amount 3949.75
        (3) 4 | control digit for amount
        (5) 12000000000023447894321689 | reference
        (6) 9: control digit for identification number and reference
        (7) 010001628: subscription number

        ISR-B (Indirect through bank)

        0100000494004> 150001123456789012345678901+ 010234567
        |/\________/|  \____/\__________________/|  \_______/
        1     2     3     4           5          6      7

        (1) 01 | header constant
        (2) 0000049400 | amount 494.00
        (3) 4 | control digit for amount
        (4) 150001 | id number of the customer (size may vary)
        (5) 12345678901234567890 | reference
        (6) 1: control digit for identification number and reference
        (7) 010234567: subscription number

        Reference will contains partner internal reference if set on the
        customer.

        :return: scan line
        :rtype: str
        """
        # pylint: enable=anomalous-backslash-in-string
        for rec in self:
            scan_line_list = rec._compute_scan_line_list()
            rec.scan_line = ''.join(scan_line_list)

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
    def _compute_pay_slips_from_move_lines(self, move_lines):
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
    def _compute_pay_slips_from_invoices(self, invoices):
        """Generate ```l10n_ch.payment_slip``` from
        ```account.invoice``` recordset

        :param move_lines: Recordset of `account.invoice`
        :type move_lines: :py:class:`openerp.models.Model`

        """
        move_lines = self.env['account.move.line'].browse()
        for invoice in invoices:
            move_lines += invoice.get_payment_move_line()
        return self._compute_pay_slips_from_move_lines(move_lines)

    def get_comm_partner(self):
        """Determine wich partner should be display
        on the payment slip

        :return: corresponding `res.partner` record
        :rtype: :py:class:`openerp.models.Model`
        """
        self.ensure_one()
        invoice = self.move_line_id.invoice_id
        if hasattr(invoice, 'commercial_partner_id'):
            return invoice.commercial_partner_id
        else:
            return invoice.partner_id

    @api.multi
    def _validate(self):
        """Check if the payment slip is ready to be printed

        :return: True or raise an exception
        :rtype: bool"""
        for rec in self:
            invoice = rec.move_line_id.invoice_id
            if not invoice:
                raise exceptions.ValidationError(
                    _('No invoice related to move line %s'
                      ) % rec.move_line_id.ref
                )

    @api.model
    def font_absolute_path(self):
        """Will get the ocrb font absolute path

        :return: path to the font
        """
        path = get_module_resource('l10n_ch_payment_slip',
                                   'static',
                                   'src',
                                   'font',
                                   'ocrbb.ttf')
        return path

    @api.model
    def image_absolute_path(self, file_name):
        """Will get image absolute path

        :param file_name: name of image

        :return: image path
        :rtype: str
        """
        path = get_module_resource('l10n_ch_payment_slip',
                                   'static',
                                   'src',
                                   'img',
                                   file_name)
        return path

    @api.model
    def _register_fonts(self):
        """Hook to register any font that can be
        needed in payment slip

        see `pdfmetrics.registerFont` doc for more details
        """
        font_identifier = 'ocrb_font'
        pdfmetrics.registerFont(TTFont(font_identifier,
                                       self.font_absolute_path()))

    @api.model
    def _get_small_text_font(self):
        """Register a :py:class:`reportlab.pdfbase.ttfonts.TTFont`
        for recept reference
        :return: a :py:class:`FontMeta` with font name and size
        :rtype: :py:class:`FontMeta`
        """
        font_identifier = 'ocrb_font'
        return FontMeta(name=font_identifier,
                        size=self._default_font_size * 0.7)

    @api.model
    def _get_text_font(self):
        """Register a :py:class:`reportlab.pdfbase.ttfonts.TTFont`
        for addresses and bank
        :return: a :py:class:`FontMeta` with font name and size
        :rtype: :py:class:`FontMeta`
        """
        font_identifier = 'ocrb_font'
        return FontMeta(name=font_identifier,
                        size=self._default_font_size)

    @api.model
    def _get_amount_font(self):
        """Register a :py:class:`reportlab.pdfbase.ttfonts.TTFont`
        for amount
        :return: a :py:class:`FontMeta` with font name and size
        :rtype: :py:class:`FontMeta`
        """
        font_identifier = 'ocrb_font'
        return FontMeta(name=font_identifier,
                        size=self._default_amount_font_size)

    @api.model
    def _get_scan_line_text_font(self, print_settings):
        """Register a :py:class:`reportlab.pdfbase.ttfonts.TTFont`
        for scan line

        :param print_settings: layouts print setting
        :type print_settings: :py:class:`PaymentSlipSettings` or subclass

        :return: a :py:class:`FontMeta` with font name and size
        :rtype: :py:class:`FontMeta`
        """
        font_identifier = 'ocrb_font'
        # pdfmetrics.registerFont(TTFont(font_identifier,
        #                                self.font_absolute_path()))
        size = (print_settings.isr_scan_line_font_size or
                self._default_scan_font_size)
        return FontMeta(name=font_identifier,
                        size=size)

    @api.model
    @tools.ormcache_context('self._uid', 'com_partner_id', keys=('lang',))
    def _get_address_lines(self, com_partner_id):
        config_param = self.env['ir.config_parameter'].sudo()
        isr_address_format = (
            config_param.get_param('isr.address.format') or ADDR_FORMAT)
        # clone the partner to not affect real partner
        com_partner = self.env['res.partner'].browse(com_partner_id)
        partner = self.env['res.partner'].new(com_partner.copy_data()[0])
        # use onchange to define our own temporary address format
        with self.env.do_in_onchange():
            # assign a fake country in case partner has no country set
            # NOTE: creating the country BEFORE assigning the format to it
            # is mandatory. If you create and assign the value at the same time
            # `address_format` won't be populated properly!
            partner.country_id = self.env['res.country'].new()
            partner.country_id.address_format = isr_address_format
            address_lines = partner._display_address(
                without_company=True).split("\n")
        return address_lines

    @api.model
    def _get_address_font_size(self, font_size, address_lines, com_partner):
        """ Return a font size and if minimun font size the max length

        :param font: font to use
        :type font: :py:class:`FontMeta`

        :returns: font_size, cutoff_length
        """
        max_line_length = max(len(l) for l in address_lines)
        if com_partner.name:
            max_line_length = max(max_line_length, len(com_partner.name))

        cutoff_length = None

        if max_line_length <= 23:
            font_size = min(11, font_size)
        elif max_line_length <= 27:
            font_size = min(10, font_size)
        elif max_line_length <= 30:
            font_size = min(9, font_size)
        else:
            # now we have smallest font, we cut off if length exceeds 34
            # characters
            cutoff_length = 34
            font_size = min(8, font_size)
        return font_size, cutoff_length

    @api.model
    def _draw_address(self, canvas, print_settings, initial_position, font,
                      com_partner):
        """Draw an address on canvas

        Address format can be changed by adding system parameter
        `isr.address.format`.

        :param canvas: payment slip reportlab component to be drawn
        :type canvas: :py:class:`reportlab.pdfgen.canvas.Canvas`

        :param print_settings: layouts print setting
        :type print_settings: :py:class:`PaymentSlipSettings` or subclass

        :para initial_position: tuple of coordinate (x, y)
        :type initial_position: tuple

        :param font: font to use
        :type font: :py:class:`FontMeta`

        :param com_partner: commercial partner record for model `res.partner`
        :type com_partner: :py:class:`openerp.models.Model`

        """
        address_lines = self._get_address_lines(com_partner.id)

        font_size, cutoff_length = self._get_address_font_size(
            font.size, address_lines, com_partner)

        x, y = initial_position
        x += print_settings.isr_add_horz * inch
        y += print_settings.isr_add_vert * inch
        text = canvas.beginText()
        text.setTextOrigin(x, y)
        text.setFont(font.name, font_size)
        if com_partner.name:
            text.textOut(com_partner.name[:cutoff_length])
        # we are moving in the original font size to new position
        text.moveCursor(0.0, font.size)
        [text.textLine(l[:cutoff_length]) for l in address_lines if l]

        canvas.drawText(text)

    @api.multi
    def _draw_description_line(self, canvas, print_settings, initial_position,
                               font):
        """ Draw a line above the payment slip

        The line shows the invoice number and payment term.

        :param canvas: payment slip reportlab component to be drawn
        :type canvas: :py:class:`reportlab.pdfgen.canvas.Canvas`

        :param print_settings: layouts print setting
        :type print_settings: :py:class:`PaymentSlipSettings` or subclass

        :para initial_position: tuple of coordinate (x, y)
        :type initial_position: tuple

        :param font: font to use
        :type font: :py:class:`FontMeta`

        """
        x, y = initial_position
        # align with the address
        x += print_settings.isr_add_horz * inch
        invoice = self.move_line_id.invoice_id
        date_maturity = self.move_line_id.date_maturity
        message = _('Payment slip related to invoice %s '
                    'due on the %s')
        fmt_date = format_date(self.env, date_maturity)
        canvas.setFont(font.name, font.size)
        canvas.drawString(x, y,
                          message % (invoice.number, fmt_date))

    @api.model
    def _draw_bank(self, canvas, print_settings, initial_position, font, bank):
        """Draw bank name, NPA and location on canvas

        :param canvas: payment slip reportlab component to be drawn
        :type canvas: :py:class:`reportlab.pdfgen.canvas.Canvas`

        :param print_settings: layouts print setting
        :type print_settings: :py:class:`PaymentSlipSettings` or subclass

        :para initial_position: tuple of coordinate (x, y)
        :type initial_position: tuple

        :param font: font to use
        :type font: :py:class:`FontMeta`

        :param bank: bank record
        :type bank: :py:class:`openerp.model.Models`

        """
        x, y = initial_position
        x += print_settings.isr_delta_horz * inch
        y += print_settings.isr_delta_vert * inch
        text = canvas.beginText()
        text.setTextOrigin(x, y)
        text.setFont(font.name, font.size)
        bank_name = textwrap.fill(bank.name, 26)
        lines = bank_name.split("\n")
        lines.append(" ".join([bank.zip or '', bank.city or '']))
        text.textOut(lines.pop(0))
        text.moveCursor(0.0, font.size)
        for line in lines:
            if not line:
                continue
            text.textLine(line)

        canvas.drawText(text)

    @api.model
    def _draw_bank_account(self, canvas, print_settings, initial_position,
                           font, acc):
        """Draw bank account on canvas


        :param canvas: payment slip reportlab component to be drawn
        :type canvas: :py:class:`reportlab.pdfgen.canvas.Canvas`

        :param print_settings: layouts print setting
        :type print_settings: :py:class:`PaymentSlipSettings` or subclass

        :para initial_position: tuple of coordinate (x, y)
        :type initial_position: tuple

        :param font: font to use
        :type font: :py:class:`FontMeta`

        :param acc: acc number
        :type acc: str

        :para initial_position: tuple of coordinate (x, y)
        :type initial_position: tuple

        """
        x, y = initial_position
        x += print_settings.isr_delta_horz * inch
        y += print_settings.isr_delta_vert * inch
        canvas.setFont(font.name, font.size)
        canvas.drawString(x, y, acc)

    @api.model
    def _draw_ref(self, canvas, print_settings, initial_position, font, ref):
        """Draw reference on canvas

        :param canvas: payment slip reportlab component to be drawn
        :type canvas: :py:class:`reportlab.pdfgen.canvas.Canvas`

        :param print_settings: layouts print setting
        :type print_settings: :py:class:`PaymentSlipSettings` or subclass

        :para initial_position: tuple of coordinate (x, y)
        :type initial_position: tuple

        :param font: font to use
        :type font: :py:class:`FontMeta`

        :param ref: ref number
        :type ref: str

        """
        x, y = initial_position
        x += print_settings.isr_delta_horz * inch
        y += print_settings.isr_delta_vert * inch
        canvas.setFont(font.name, font.size)
        canvas.drawString(x, y, ref)

    @api.model
    def _draw_recipe_ref(self, canvas, print_settings, initial_position,
                         font, ref):
        """Draw recipe reference on canvas

        :param canvas: payment slip reportlab component to be drawn
        :type canvas: :py:class:`reportlab.pdfgen.canvas.Canvas`

        :param print_settings: layouts print setting
        :type print_settings: :py:class:`PaymentSlipSettings` or subclass

        :para initial_position: tuple of coordinate (x, y)
        :type initial_position: tuple

        :param font: font to use
        :type font: :py:class:`FontMeta`

        :param ref: ref number
        :type ref: str

        """
        x, y = initial_position
        x += print_settings.isr_add_horz * inch
        y += print_settings.isr_add_vert * inch
        canvas.setFont(font.name, font.size)
        canvas.drawString(x, y, ref)

    @api.model
    def _draw_amount(self, canvas, print_settings, initial_position,
                     font, amount):
        """Draw reference on canvas

        :param canvas: payment slip reportlab component to be drawn
        :type canvas: :py:class:`reportlab.pdfgen.canvas.Canvas`

        :param print_settings: layouts print setting
        :type print_settings: :py:class:`PaymentSlipSettings` or subclass

        :para initial_position: tuple of coordinate (x, y)
        :type initial_position: tuple

        :param font: font to use
        :type font: :py:class:`FontMeta`

        :param amount: amount to print
        :type amount: str

        """
        x, y = initial_position
        x += (print_settings.isr_delta_horz * inch +
              print_settings.isr_amount_line_horz * inch)
        y += (print_settings.isr_delta_vert * inch +
              print_settings.isr_amount_line_vert * inch)
        indice = 0
        canvas.setFont(font.name, font.size)
        for car in amount[::-1]:
            width = canvas.stringWidth(car, font.name, font.size)
            if indice:
                # some font type return non numerical
                x -= float(width) / 2.0
            canvas.drawString(x, y, car)
            x -= 0.06 * inch + float(width) / 2.0
            indice += 1

    @api.model
    def _draw_scan_line(self, canvas, print_settings, initial_position, font):
        """Draw reference on canvas


        :param canvas: payment slip reportlab component to be drawn
        :type canvas: :py:class:`reportlab.pdfgen.canvas.Canvas`

        :param print_settings: layouts print setting
        :type print_settings: :py:class:`PaymentSlipSettings` or subclass

        :para initial_position: tuple of coordinate (x, y)
        :type initial_position: tuple

        :param font: font to use
        :type font: :py:class:`FontMeta`

        """
        x, y = initial_position
        x += print_settings.isr_scan_line_horz * inch
        y += print_settings.isr_scan_line_vert * inch
        canvas.setFont(font.name, font.size)
        for car in self._compute_scan_line_list()[::-1]:
            canvas.drawString(x, y, car)
            # some font type return non numerical
            x -= 0.1 * inch

    @api.model
    def _draw_background(self, canvas, print_settings):
        """Draw payment slip background based on company setting

        :param canvas: payment slip reportlab component to be drawn
        :type canvas: :py:class:`reportlab.pdfgen.canvas.Canvas`

        :param print_settings: layouts print setting
        :type print_settings: :py:class:`PaymentSlipSettings` or subclass

        """
        if print_settings.isr_background:
            canvas.drawImage(self.image_absolute_path('isr.png'),
                             0, 0, 8.271 * inch, 4.174 * inch)

    @api.model
    def _draw_hook(self, draw, print_settings):
        """Hook to add your own content on canvas"""
        pass

    @api.model
    def _get_settings(self, report_name):
        company = self.env.user.company_id
        company_settings = {
            col: getattr(company, col) for col in company._fields if
            col.startswith('isr_')
        }
        return PaymentSlipSettings(report_name, **company_settings)

    def _draw_payment_slip(self, a4=False, out_format='PDF', scale=None,
                           b64=False, report_name=None):
        """Generate the payment slip image
        :param a4: If set to True will print on slip on a A4 paper format
        :type a4: bool

        :param out_format: output format at current time only PDF is supported
        :type out_format: str

        :param scale: scale quadratic ration
        :type scale: float

        :param b64: If set to True the output image string
                    will be encoded to base64

        :return: slip image string
        :rtype: str
        """
        if out_format != 'PDF':
            raise NotImplementedError(
                'Only PDF payment slip are supported'
            )
        self.ensure_one()
        lang = self.invoice_id.partner_id.lang
        self = self.with_context(lang=lang)
        company = self.env.user.company_id
        print_settings = self._get_settings(report_name)
        self._register_fonts()
        default_font = self._get_text_font()
        small_font = self._get_small_text_font()
        amount_font = self._get_amount_font()
        invoice = self.move_line_id.invoice_id
        scan_font = self._get_scan_line_text_font(company)
        isr_subs_number = invoice.l10n_ch_isr_subscription_formatted
        bank_acc = invoice.partner_bank_id
        if a4:
            canvas_size = (595.27, 841.89)
        else:
            canvas_size = (595.27, 286.81)
        with contextlib.closing(io.BytesIO()) as buff:
            canvas = Canvas(buff,
                            pagesize=canvas_size,
                            pageCompression=None)
            self._draw_background(canvas, print_settings)
            canvas.setFillColorRGB(*self._fill_color)
            if a4:
                initial_position = (0.05 * inch, 4.50 * inch)
                self._draw_description_line(canvas,
                                            print_settings,
                                            initial_position,
                                            default_font)
            if invoice.partner_bank_id.print_partner:
                if (invoice.partner_bank_id.print_account or
                        invoice.l10n_ch_isr_subscription):
                    initial_position = (0.05 * inch, 3.30 * inch)
                else:
                    initial_position = (0.05 * inch, 3.75 * inch)
                self._draw_address(canvas, print_settings, initial_position,
                                   default_font, company.partner_id)
                if (invoice.partner_bank_id.print_account or
                        invoice.l10n_ch_isr_subscription):
                    initial_position = (2.45 * inch, 3.30 * inch)
                else:
                    initial_position = (2.45 * inch, 3.75 * inch)
                self._draw_address(canvas, print_settings, initial_position,
                                   default_font, company.partner_id)
            com_partner = self.get_comm_partner()
            initial_position = (0.05 * inch, 1.4 * inch)
            self._draw_address(canvas, print_settings, initial_position,
                               default_font, com_partner)
            initial_position = (4.86 * inch, 2.2 * inch)
            self._draw_address(canvas, print_settings, initial_position,
                               default_font, com_partner)
            num_car, frac_car = ("%.2f" % self.amount_total).split('.')
            self._draw_amount(canvas, print_settings,
                              (1.48 * inch, 2.0 * inch),
                              amount_font, num_car)
            self._draw_amount(canvas, print_settings,
                              (2.14 * inch, 2.0 * inch),
                              amount_font, frac_car)
            self._draw_amount(canvas, print_settings,
                              (3.88 * inch, 2.0 * inch),
                              amount_font, num_car)
            self._draw_amount(canvas, print_settings,
                              (4.50 * inch, 2.0 * inch),
                              amount_font, frac_car)
            if invoice.partner_bank_id.print_bank:
                self._draw_bank(canvas,
                                print_settings,
                                (0.05 * inch, 3.75 * inch),
                                default_font,
                                bank_acc.bank_id)
                self._draw_bank(canvas,
                                print_settings,
                                (2.45 * inch, 3.75 * inch),
                                default_font,
                                bank_acc.bank_id)
            if invoice.partner_bank_id.print_account:
                self._draw_bank_account(canvas,
                                        print_settings,
                                        (1 * inch, 2.35 * inch),
                                        default_font,
                                        isr_subs_number)
                self._draw_bank_account(canvas,
                                        print_settings,
                                        (3.4 * inch, 2.35 * inch),
                                        default_font,
                                        isr_subs_number)

            if print_settings.isr_header_partner_address:
                self._draw_address(canvas, print_settings,
                                   (4.9 * inch, 9.0 * inch),
                                   default_font, com_partner)

            self._draw_ref(canvas,
                           print_settings,
                           (4.9 * inch, 2.70 * inch),
                           default_font,
                           self.reference)
            self._draw_recipe_ref(canvas,
                                  print_settings,
                                  (0.05 * inch, 1.6 * inch),
                                  small_font,
                                  self.reference)
            self._draw_scan_line(canvas,
                                 print_settings,
                                 (8.26 * inch - 4 / 10 * inch, 4 / 6 * inch),
                                 scan_font)
            self._draw_hook(canvas, print_settings)
            canvas.showPage()
            canvas.save()
            img_stream = buff.getvalue()
            if b64:
                img_stream = base64.encodestring(img_stream)
            return img_stream

    def _compute_payment_slip_image(self):
        """Draw an us letter format slip in PNG"""
        img = self._draw_payment_slip()
        self.slip_image = base64.encodestring(img)
        return img

    def _compute_a4_report(self):
        """Draw an a4 format slip in PDF"""
        img = self._draw_payment_slip(a4=True, out_format='PDF')
        self.a4_pdf = base64.encodestring(img)
        return img
