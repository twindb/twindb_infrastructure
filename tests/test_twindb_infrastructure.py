#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_twindb_infrastructure
----------------------------------

Tests for `twindb_infrastructure` module.
"""


from click.testing import CliRunner

from twindb_infrastructure import cli
from twindb_infrastructure.twindb_infra import show


def test_command_line_interface():
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'twindb_infrastructure.cli.main' in result.output
    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output


def test_show():
    assert show()
