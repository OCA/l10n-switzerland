# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import unidecode


def sanitize_string(string):
    """Remove all non ascii char"""
    return unidecode.unidecode(string)


def get_single_option(picking, option):
    """Get an option from picking or from company"""
    option = [opt.code for opt in picking.option_ids if opt.quickpac_type == option]
    assert len(option) <= 1
    return option and option[0]


def get_label_layout(picking):
    label_layout = get_single_option(picking, "label_layout")
    if not label_layout:
        company = picking.company_id
        label_layout = company.quickpac_label_layout.code
    return label_layout


def get_output_format(picking):
    output_format = get_single_option(picking, "output_format")
    if not output_format:
        company = picking.company_id
        output_format = company.quickpac_output_format.code
    return output_format


def get_image_resolution(picking):
    resolution = get_single_option(picking, "resolution")
    if not resolution:
        company = picking.company_id
        resolution = company.quickpac_resolution.code
    return resolution


def get_logo(picking):
    logo = get_single_option(picking, "logo")
    if not logo:
        company = picking.company_id
        logo = company.quickpac_logo
    return logo


def get_language(lang, default_lang="de"):
    """Return a language to iso format from odoo format.

    `iso_code` field in res.lang is not mandatory thus not always set.
    Use partner language if available, otherwise use english

    :param lang: the lang to map
    :param default_lang: the default lang
    :return: language code to use.
    """
    if not lang:
        lang = default_lang
    available_languages = ["de", "en", "fr", "it"]  # Given by API doc
    lang_code = lang.split("_")[0]
    if lang_code in available_languages:
        return lang_code
    return default_lang
