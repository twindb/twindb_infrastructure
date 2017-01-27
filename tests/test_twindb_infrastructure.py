#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_twindb_infrastructure
----------------------------------

Tests for `twindb_infrastructure` module.
"""
import logging

from click.testing import CliRunner
import mock
import pytest

from twindb_infrastructure import cli, setup_logging
from twindb_infrastructure.util import printf


def test_command_line_interface():
    runner = CliRunner()
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert 'twindb_infrastructure.cli.main' in result.output

    help_result = runner.invoke(cli.main, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output


@mock.patch('twindb_infrastructure.util.sys')
def test_printf(mock_sys):
    printf('foo')
    mock_sys.stdout.write.assert_called_once_with('foo')


@pytest.mark.parametrize('debug,level', [
    (
        False,
        logging.INFO
    ),
    (
        True,
        logging.DEBUG
    ),
])
def test_setup_logging(debug, level):
    logger = logging.getLogger(__name__)
    setup_logging(logger, debug=debug)
    assert logger.level == level
