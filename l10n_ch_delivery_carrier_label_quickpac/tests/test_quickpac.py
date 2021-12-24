# Copyright 2021 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from os.path import dirname, join

from vcr import VCR

from odoo.exceptions import UserError
from odoo.tests import common

recorder = VCR(
    record_mode="once",
    cassette_library_dir=join(dirname(__file__), "fixtures/cassettes"),
    path_transformer=VCR.ensure_suffix(".yaml"),
    filter_headers=["Authorization"],
    filter_post_data_parameters=["username", "password"],
    # ignore scheme, host, port
    match_on=("method", "path", "query"),
    # allow to read and edit content in cassettes
    decode_compressed_response=True,
)

USERNAME = "XXXXX"
PASSWORD = "XXXXX"
FRANKING_LICENSE = "XXXXXX"


class TestQuickpac(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Product = cls.env["product.product"]
        partner_id = cls.env.ref(
            "l10n_ch_delivery_carrier_label_quickpac.partner_quickpac"
        ).id
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Quickpac",
                "delivery_type": "quickpac",
                "product_id": Product.create({"name": "Shipping"}).id,
            }
        )
        OptionTmpl = cls.env["delivery.carrier.template.option"]

        service_opt_tmpl = OptionTmpl.create({"code": "PRI"})
        label_layout = OptionTmpl.create({"code": "A6", "partner_id": partner_id})
        output_format = OptionTmpl.create({"code": "PDF", "partner_id": partner_id})
        image_resolution = OptionTmpl.create({"code": "600", "partner_id": partner_id})

        Option = cls.env["delivery.carrier.option"]
        service_opt = Option.create(
            {
                "code": "PRI",
                "partner_id": partner_id,
                "quickpac_type": "basic",
                "tmpl_option_id": service_opt_tmpl.id,
            }
        )

        cls.env.user.company_id.write(
            {
                "quickpac_username": USERNAME,
                "quickpac_password": PASSWORD,
                "quickpac_franking_license": FRANKING_LICENSE,
                "quickpac_label_layout": label_layout.id,
                "quickpac_output_format": output_format.id,
                "quickpac_resolution": image_resolution.id,
                "street": "Rue de Lausanne 1",
                "zip": "1030",
                "city": "Bussigny",
            }
        )
        cls.env.user.company_id.partner_id.country_id = cls.env.ref("base.ch")
        stock_location = cls.env.ref("stock.stock_location_stock")
        customer_location = cls.env.ref("stock.stock_location_customers")
        Picking = cls.env["stock.picking"].with_context(active_test=True)
        recipient = cls.env["res.partner"].create(
            {
                "name": "Camptocamp SA",
                "street": "",
                "zip": "4536",
                "city": "Attiswil",
            }
        )
        cls.valid_recipient = cls.env["res.partner"].create(
            {
                "name": "Camptocamp SA",
                "street": "",
                "zip": "3372",
                "city": "Heimenhausen",
            }
        )
        cls.invalid_recipient = cls.env["res.partner"].create(
            {
                "name": "Camptocamp SA",
                "street": "",
                "zip": "50200",
                "city": "Bricqueville-la-Blouette",
            }
        )
        cls.picking = Picking.create(
            {
                "partner_id": recipient.id,
                "carrier_id": cls.carrier.id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "location_id": stock_location.id,
                "location_dest_id": customer_location.id,
                "option_ids": [(4, service_opt.id, 0)],
            }
        )
        product = Product.create({"name": "Product A"})

        cls.env["stock.move"].create(
            {
                "name": "a move",
                "product_id": product.id,
                "product_uom_qty": 3.0,
                "product_uom": product.uom_id.id,
                "picking_id": cls.picking.id,
                "location_id": stock_location.id,
                "location_dest_id": customer_location.id,
            }
        )
        cls.env.user.lang = "en_US"
        # creating the default package requires to have move lines
        # in addition, Check Availbility is enabled when picking state is "confirmed",
        # thus the picking must be confirmed
        cls.picking.action_confirm()
        # send_to_shipper calls _set_a_default_package already

    def test_store_label(self):
        """Test the whole label workflow"""
        self.picking._set_a_default_package()
        self.assertEqual(self.picking.state, "assigned")
        package = self.picking.package_ids[0]
        self.assertFalse(package.parcel_tracking)
        with recorder.use_cassette("test_store_label") as cassette:  # noqa: F841
            res = self.picking._generate_quickpac_label()
            ref = "440010370000000023"
            self.assertEqual(res[0]["file_type"], "pdf")
            self.assertEqual(res[0]["name"], "{}.pdf".format(ref))
            self.assertEqual(res[0]["file"][:30], b"JVBERi0xLjQKJdP0zOEKMSAwIG9iag")
            self.assertEqual(res[0]["tracking_number"], ref)

    def test_all_possible_values(self):
        recipient = self.picking.partner_id
        recipient.parent_id = self.valid_recipient
        vals = {
            "name": self.valid_recipient.name + " Test",
            "country_id": self.env.ref("base.ch").id,
            "street2": "Street 2",
            "phone": "0123456789",
            "mobile": "0987654321",
        }
        self.valid_recipient.write(vals)
        OptionTmpl = self.env["delivery.carrier.template.option"]
        service_opt_tmpl = OptionTmpl.create({"code": "ZAW3213"})
        Option = self.env["delivery.carrier.option"]
        qp_xmlid = "l10n_ch_delivery_carrier_label_quickpac.partner_quickpac"
        service_opt = Option.create(
            {
                "code": "ZAW3213",
                "partner_id": self.env.ref(qp_xmlid).id,
                "quickpac_type": "basic",
                "tmpl_option_id": service_opt_tmpl.id,
            }
        )
        self.picking.option_ids |= service_opt
        self.assertEqual(self.picking.state, "assigned")
        self.assertFalse(self.picking.package_ids)
        with recorder.use_cassette("test_store_label") as cassette:  # noqa: F841
            self.picking.send_to_shipper()
        ref = "440010370000000023"
        url = self.carrier.get_tracking_link(self.picking)
        package = self.picking.package_ids[0]
        self.assertEqual(package.parcel_tracking, ref)
        self.assertEqual(url, "https://quickpac.ch/en/tracking/" + ref)

    def test_use_tracking_num(self):
        self.picking.company_id.quickpac_tracking_format = "picking_num"
        with recorder.use_cassette("test_store_label") as cassette:  # noqa: F841
            self.picking.send_to_shipper()
        self.carrier.quickpac_get_tracking_link(self.picking)

    def test_valid_zipcode(self):
        """Test that zipcode is correct when changing for an valid partner"""
        with recorder.use_cassette("test_valid_zipcode") as cassette:  # noqa: F841
            self.picking.partner_id = self.valid_recipient
            self.picking.onchange_carrier_id()
            self.assertEqual(cassette.play_count, 1)

    def test_invalid_zipcode(self):
        """Test that zipcode is incorrect when changing for an invalid partner"""
        self.picking.partner_id = self.invalid_recipient
        with recorder.use_cassette("test_invalid_zipcode") as cassette:  # noqa: F841
            self.assertRaises(UserError, self.picking.onchange_carrier_id)
            self.assertEqual(cassette.play_count, 1)
