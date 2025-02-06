import os
from io import StringIO
from pathlib import Path
from unittest import mock

from django.core.management import call_command
from django.core.management.base import CommandError

from tests.testcases import DjangoSetupTestCase


def get_mock_path(is_dir=False, is_file=False, is_true=False):
    """Creates a mock Path object that has scoped parameters."""

    class MockPath(mock.Mock):
        # Use Mock and not MagicMock so that magic methods can be provided.
        def __init__(self, *args, **kwargs):
            kwargs["spec_set"] = Path
            super().__init__(*args, **kwargs)

        def __truediv__(self, other):
            return MockPath()

        def __bool__(self):
            return is_true

        def is_dir(self):
            return is_dir

        def is_file(self):
            return is_file

    return MockPath()


class CommandTests(DjangoSetupTestCase):

    def call_command(self, *args, **kwargs):
        out = StringIO()
        err = StringIO()
        call_command(
            "nomad",
            *args,
            stdout=out,
            stderr=err,
            **kwargs,
        )
        return out.getvalue(), err.getvalue()

    @mock.patch(
        "django_nomad.management.commands.nomad.Path",
        get_mock_path(is_dir=True, is_true=True, is_file=False),
    )
    @mock.patch("django_nomad.management.commands.nomad.shutil.copy")
    def test_install(self, mock_copy):
        out, err = self.call_command("install", "/a/destination/")

        self.assertTrue(out.startswith("git hook created: "))
        self.assertEqual(err, "")

        mock_copy.assert_called_once()

    @mock.patch(
        "django_nomad.management.commands.nomad.Path", get_mock_path(is_dir=False)
    )
    def test_install_not_git_dir(self):
        with self.assertRaises(CommandError) as context:
            self.call_command("install", "/a/destination/")
        msg = str(context.exception)
        self.assertTrue("does not appear to contain a git repo" in msg)

    @mock.patch(
        "django_nomad.management.commands.nomad.Path",
        get_mock_path(is_dir=True, is_true=False),
    )
    def test_install_no_githooks_path(self):
        with self.assertRaises(CommandError) as context:
            self.call_command("install", "/a/destination/")
        msg = str(context.exception)
        self.assertTrue("does not contain a 'hooks' directory" in msg)

    @mock.patch(
        "django_nomad.management.commands.nomad.Path",
        get_mock_path(is_dir=True, is_true=True, is_file=True),
    )
    def test_install_file_already_exists(self):
        with self.assertRaises(CommandError) as context:
            self.call_command("install", "/a/destination/")
        msg = str(context.exception)
        self.assertTrue("already contains a post-checkout hook" in msg)

    @mock.patch("django_nomad.management.commands.nomad.stage_one")
    def test_migrate_stage_one(self, mock_stage_one):
        out, err = self.call_command("migrate")
        self.assertEqual(err, "")

        mock_stage_one.assert_called_once()

    @mock.patch.dict(os.environ, {"DJANGO_NOMAD_STAGE": "TWO"})
    @mock.patch("django_nomad.management.commands.nomad.stage_two")
    def test_migrate_stage_two(self, mock_stage_two):
        out, err = self.call_command("migrate")
        self.assertEqual(err, "")

        mock_stage_two.assert_called_once()

    @mock.patch.dict(os.environ, {"DJANGO_NOMAD_STAGE": "THREE"})
    @mock.patch("django_nomad.management.commands.nomad.stage_three")
    def test_migrate_stage_three(self, mock_stage_three):
        out, err = self.call_command("migrate")
        self.assertEqual(err, "")

        mock_stage_three.assert_called_once()
        mock_stage_three.assert_called_once()
