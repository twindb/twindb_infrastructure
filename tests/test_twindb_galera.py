from click.testing import CliRunner

from twindb_infrastructure import twindb_galera


def test_main():
    runner = CliRunner()
    result = runner.invoke(twindb_galera.main)
    assert result.exit_code == 0
