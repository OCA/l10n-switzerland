# -*- coding: utf-8 -*-
# Copyright 2019-2020 Odoo
# Copyright 2019-2020 Camptocamp SA
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from werkzeug import exceptions

from odoo.http import Controller, route, request


class ReportController(Controller):

    # ------------------------------------------------------
    # Misc. route utils
    # ------------------------------------------------------
    @route(
        ['/report/qrcode', '/report/qrcode/<path:value>'],
        type='http',
        auth="public",
    )
    def report_qrcode(self, value, width=600, height=100, bar_border=4):
        """Contoller able to render barcode images thanks to reportlab.

        This adds `bar_border` capability.

        Samples:
            <img t-att-src="'/report/qrcode/%s' % o.name"/>
            <img t-att-src="'/report/qrcode/?value=%s&amp;width=%s&amp;height=%s' %
                (o.name, 200, 200)"/>

        :param bar_border: Size of blank border, use 0 to remove border.
        """
        try:
            qrcode = request.env['report'].qrcode(
                value, width=width, height=height, bar_border=bar_border
            )
        except (ValueError, AttributeError):
            raise exceptions.HTTPException(
                description='Cannot convert into qrcode.'
            )

        return request.make_response(
            qrcode, headers=[('Content-Type', 'image/png')]
        )
