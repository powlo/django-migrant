from unittest import mock

from django_migrant.management.commands import migrant
from tests.testcases import DjangoSetupTestCase


class TestStageOne(DjangoSetupTestCase):

    @mock.patch("django_migrant.management.commands.migrant.subprocess", mock.MagicMock())
    @mock.patch("django_migrant.management.commands.migrant.Path", mock.MagicMock())
    @mock.patch("django_migrant.management.commands.migrant.MigrationLoader")
    def test_file_written(self, mock_loader):
        mock_loader.return_value.applied_migrations = [
            ("polls", "0002_alter_question_question_text"),
            ("polls", "0001_initial"),
        ]

        mock_loader.return_value.disk_migrations = [
            ("polls", "0001_initial"),
        ]

        with mock.patch("builtins.open", mock.mock_open()) as mock_open:
            migrant.stage_one()
        handle = mock_open()
        handle.write.assert_called_once_with(
            '[["polls", "0002_alter_question_question_text"]]'
        )

    @mock.patch("django_migrant.management.commands.migrant.Path", mock.MagicMock())
    @mock.patch(
        "django_migrant.management.commands.migrant.MigrationLoader", mock.MagicMock()
    )
    @mock.patch("django_migrant.management.commands.migrant.subprocess")
    def test_subprocess_called(self, mock_subprocess):

        with mock.patch("builtins.open", mock.mock_open()):
            migrant.stage_one()

        # Subprocess was called.
        mock_subprocess.run.assert_called_once()
        self.assertEqual(len(mock_subprocess.run.call_args), 2)

        # And was called with git checkout.
        call_args = mock_subprocess.run.call_args
        first_arg = call_args[0]
        self.assertEqual(first_arg[0], ["git", "checkout", "-", "--quiet"])

        # And env var is set to stage two.
        second_arg = call_args[1]
        self.assertTrue("env" in second_arg)
        self.assertTrue("django_migrant_STAGE" in second_arg["env"])
        self.assertEqual(second_arg["env"]["django_migrant_STAGE"], "TWO")
