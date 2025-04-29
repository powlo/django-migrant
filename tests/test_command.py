import os
import sys
from importlib import resources
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
            "migrant",
            *args,
            stdout=out,
            stderr=err,
            **kwargs,
        )
        return out.getvalue(), err.getvalue()

    @mock.patch(
        "django_migrant.management.commands.migrant.Path",
        get_mock_path(is_dir=True, is_true=True, is_file=False),
    )
    def test_install(self):

        # This replicates what we expect to happen in script, because in order
        # to mock the write we have to also mock the read. But we want the read
        # to behave as normal.
        src_post_checkout_file = (
            resources.files("django_migrant") / "hook_templates" / "post-checkout"
        )

        with open(src_post_checkout_file, "r") as fh:
            template = fh.read()

        mock_open = mock.mock_open(read_data=template)
        with mock.patch("django_migrant.management.commands.migrant.open", mock_open):
            out, err = self.call_command("install", "/a/destination/")

        handle = mock_open()
        handle.write.assert_called_once()

        self.assertTrue(sys.executable in handle.write.call_args[0][0])
        self.assertTrue(out.startswith("git hook created: "))
        self.assertEqual(err, "")

    @mock.patch(
        "django_migrant.management.commands.migrant.Path", get_mock_path(is_dir=False)
    )
    def test_install_not_git_dir(self):
        with self.assertRaises(CommandError) as context:
            self.call_command("install", "/a/destination/")
        msg = str(context.exception)
        self.assertTrue("does not appear to contain a git repo" in msg)

    @mock.patch(
        "django_migrant.management.commands.migrant.Path",
        get_mock_path(is_dir=True, is_true=False),
    )
    def test_install_no_githooks_path(self):
        with self.assertRaises(CommandError) as context:
            self.call_command("install", "/a/destination/")
        msg = str(context.exception)
        self.assertTrue("does not contain a 'hooks' directory" in msg)

    @mock.patch(
        "django_migrant.management.commands.migrant.Path",
        get_mock_path(is_dir=True, is_true=True, is_file=True),
    )
    def test_install_file_already_exists(self):
        with self.assertRaises(CommandError) as context:
            self.call_command("install", "/a/destination/")
        msg = str(context.exception)
        self.assertTrue("already contains a post-checkout hook" in msg)

    @mock.patch("django_migrant.management.commands.migrant.stage_one")
    def test_migrate_stage_one(self, mock_stage_one):
        out, err = self.call_command("migrate")
        self.assertEqual(err, "")

        mock_stage_one.assert_called_once()

    @mock.patch.dict(os.environ, {"django_migrant_STAGE": "TWO"})
    @mock.patch("django_migrant.management.commands.migrant.stage_two")
    def test_migrate_stage_two(self, mock_stage_two):
        out, err = self.call_command("migrate")
        self.assertEqual(err, "")

        mock_stage_two.assert_called_once()

    @mock.patch.dict(os.environ, {"django_migrant_STAGE": "THREE"})
    @mock.patch("django_migrant.management.commands.migrant.stage_three")
    def test_migrate_stage_three(self, mock_stage_three):
        out, err = self.call_command("migrate")
        self.assertEqual(err, "")

        mock_stage_three.assert_called_once()
        mock_stage_three.assert_called_once()
