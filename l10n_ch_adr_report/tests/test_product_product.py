# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase


class TestProductProduct(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_category = cls.env["product.category"].create(
            {
                "name": "Test Category",
            }
        )
        cls.adr_goods = cls.env.ref(
            "l10n_eu_product_adr.adr_goods_0004_1dot1D_1_P112a/P112b/P112c_1"
        )
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "list_price": 20.0,
                "nag": "N.A.G 1",
                "label_first": "1",
                "label_second": "2",
                "label_third": "3",
                "packaging_group": "3",
                "envir_hazardous": "yes",
                "categ_id": cls.product_category.id,
                "adr_goods_id": cls.adr_goods.id,
            }
        )

    def test_get_name_from_selection(self):
        label_first = self.product._get_name_from_selection("label_first")
        self.assertEqual(label_first, "2")
        label_second = self.product._get_name_from_selection("label_second")
        self.assertEqual(label_second, "2.1")
        packaging_group = self.product._get_name_from_selection("packaging_group")
        self.assertEqual(packaging_group, "II")

    def test_compute_adr_report_class_display_name(self):
        self.product._compute_adr_report_class_display_name()
        self.assertTrue(self.product.adr_goods_id)
        adr_report_class_display_name = self.product.adr_report_class_display_name
        first_item = adr_report_class_display_name.split()[0]
        self.assertEqual(first_item, "UN")
        items_name = adr_report_class_display_name.split(", ")
        self.assertEqual(f"{first_item} {self.adr_goods.un_number}", items_name[0])
        self.assertIn("II", items_name)
        self.assertIn("Environmentally hazardous", items_name)
