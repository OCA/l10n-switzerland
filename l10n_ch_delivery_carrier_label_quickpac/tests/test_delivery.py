# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.exceptions import UserError
from odoo.tests import common

SINGLE_OPTION_TYPES = ['label_layout', 'output_format', 'resolution']


class TestDelivery(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.carrier = cls.env['delivery.carrier'].create(
            {
                'name': "TEST CARRIER",
                'delivery_type': 'quickpac',
                'product_id': cls.env.ref(
                    'l10n_ch_delivery_carrier_label_quickpac.product_quickpac_service'
                ).id,
            }
        )
        cls.carrier_option = cls.create_carrier_option()

    @classmethod
    def create_carrier_option(cls, template=False, values=None):
        vals = {
            'name': "OPTION",
            # 'quickpac_type': 'basic',
        }
        option_model = cls.env['delivery.carrier.option']
        if template:
            option_model = cls.env['delivery.carrier.template.option']
            vals['name'] = "TEMPLATE OPTION"
        if values:
            vals.update(values)
        return option_model.create(vals)

    def test_picking_options_applied(self):
        """Check application of options on delivery picking"""
        mandatory_tmpl_option = self.create_carrier_option(
            template=True, values={'name': 'MANDATORY OPTION'}
        )
        default_tmpl_option = self.create_carrier_option(
            template=True, values={'name': 'DEFAULT OPTION'}
        )
        facultative_tmpl_option = self.create_carrier_option(
            template=True, values={'name': 'FACULTATIVE OPTION'}
        )
        self.assertEqual(len(self.carrier.available_option_ids), 0)
        mandatory_option = self.env['delivery.carrier.option'].create(
            {
                'tmpl_option_id': mandatory_tmpl_option.id,
                'mandatory': True,
                'carrier_id': self.carrier.id,
            }
        )
        default_option = self.env['delivery.carrier.option'].create(
            {
                'tmpl_option_id': default_tmpl_option.id,
                'by_default': True,
                'carrier_id': self.carrier.id,
            }
        )
        facultative_option = self.env['delivery.carrier.option'].create(
            {
                'tmpl_option_id': facultative_tmpl_option.id,
                'carrier_id': self.carrier.id,
            }
        )
        self.assertEqual(len(self.carrier.available_option_ids), 3)
        sale_order = self.env['sale.order'].create(
            {
                'partner_id': self.env.ref('base.res_partner_1').id,
                'carrier_id': self.carrier.id,
                'order_line': [
                    (
                        0,
                        0,
                        {
                            'product_id': self.env.ref(
                                'product.product_product_3'
                            ).id
                        },
                    )
                ],
            }
        )
        self.assertEqual(len(sale_order.picking_ids), 0)
        sale_order.action_confirm()
        self.assertEqual(len(sale_order.picking_ids), 1)
        picking = sale_order.picking_ids
        # check mandatory and default options are applied but not facultative
        self.assertIn(mandatory_option.id, picking.option_ids.ids)
        self.assertIn(default_option.id, picking.option_ids.ids)
        self.assertNotIn(facultative_option.id, picking.option_ids.ids)
        # Adding facultative option is ok
        picking.write({'option_ids': [(4, facultative_option.id, False)]})
        picking.onchange_option_ids()
        self.assertIn(facultative_option.id, picking.option_ids.ids)
        # Removing a facultative option is ok
        picking.write({'option_ids': [(3, facultative_option.id, 0)]})
        picking.onchange_option_ids()
        # Removing a mandatory option is not ok
        picking.write({'option_ids': [(3, mandatory_option.id, 0)]})
        with self.assertRaises(UserError):
            picking.onchange_option_ids()
        # Adding another option is not ok
        picking.write({'option_ids': [(4, self.carrier_option.id, 0)]})
        with self.assertRaises(UserError):
            picking.onchange_option_ids()
