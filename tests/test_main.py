from unittest import mock

from tests.testcases import DjangoSetupTestCase


class MainTests(DjangoSetupTestCase):
    # Test invocation of command directly, not via django-admin.
    @mock.patch("sys.argv", ["1", "2", "3"])
    @mock.patch("django_migrant.management.commands.migrant.Command")
    def test_simple(self, mock_command):
        # Trick python into invoking __main__ code.
        from django_migrant import __main__  # noqa: F401

        mock_command.assert_called_once()
        mock_command.return_value.run_from_argv.assert_called_with
        mock_command.return_value.run_from_argv.assert_called_with(
            ["django-admin", "migrant", "2", "3"]
        )
