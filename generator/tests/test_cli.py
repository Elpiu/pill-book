from typer.testing import CliRunner

from bookpack.cli import app


def test_help_runs():
    result = CliRunner().invoke(app, ["--help"])
    assert result.exit_code == 0
