# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from os.path import dirname, join

from vcr import VCR


def compare_xml_line_by_line(content, expected):
    """This a quick way to check the diff line by line to ease debugging"""
    generated_line = [l.strip() for l in content.split(b"\n") if len(l.strip())]
    expected_line = [l.strip() for l in expected.split(b"\n") if len(l.strip())]
    number_of_lines = len(expected_line)
    for i in range(number_of_lines):
        if generated_line[i].strip() != expected_line[i].strip():
            return "Diff at {}/{} || Expected {}  || Generated {}".format(
                i, number_of_lines, expected_line[i], generated_line[i],
            )


def get_recorder(base_path=None, **kw):
    base_path = base_path or dirname(__file__)
    defaults = dict(
        record_mode="once",
        cassette_library_dir=join(base_path, "fixtures/cassettes"),
        path_transformer=VCR.ensure_suffix(".yaml"),
        match_on=["method", "path", "query"],
        filter_headers=["Authorization"],
        decode_compressed_response=True,
    )
    defaults.update(kw)
    return VCR(**defaults)


recorder = get_recorder()
