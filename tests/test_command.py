import os
from importlib import resources
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
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

    def test_install(self):

        templates_dir = resources.files("django_migrant") / "hook_templates"

        with open(templates_dir / "header", "r") as fh:
            header = fh.read()

        with TemporaryDirectory() as temp_dir_name:
            hooks_path = Path(temp_dir_name) / ".git" / "hooks"
            hooks_path.mkdir(parents=True)
            out, err = self.call_command("install", temp_dir_name)

            with open(hooks_path / "post-checkout") as fh:
                contents = fh.read()
                self.assertTrue(contents.startswith(header[:9]))
                # A phrase we definitely expect to see in the hook.
                self.assertTrue("./manage.py migrant migrate" in contents)

            with open(hooks_path / "pre-rebase") as fh:
                contents = fh.read()
                self.assertTrue(contents.startswith(header[:9]))
                self.assertTrue('echo "REBASE" > .migrant' in contents)

        output = out.split("\n")
        # Remove the runt line.
        output = [x for x in output if x]
        self.assertEqual(len(output), 2)
        # The order of output doesn't really matter.
        self.assertTrue(output[0].startswith("post-checkout hook created: "))
        self.assertTrue(output[1].startswith("pre-rebase hook created: "))
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
    @mock.patch("builtins.input")
    def test_install_file_exists_dont_append(self, mock_input):
        # User presses 'N' when asked to append.
        mock_input.return_value = "N"
        with self.assertRaises(CommandError) as context:
            self.call_command("install", "/a/destination/")
        msg = str(context.exception)
        self.assertTrue("already contains a post-checkout hook" in msg)

    @mock.patch("builtins.input")
    def test_install_file_exists_do_append(self, mock_input):
        # Check behaviour when appending to an existing hook.

        # User presses 'y' when asked to append.
        mock_input.return_value = "y"

        # Prepare an existing post-checkout hook
        # Perhaps this is a better than the get_mock_path approach?
        with TemporaryDirectory() as temp_dir_name:
            hooks_path = Path(temp_dir_name) / ".git" / "hooks"
            hooks_path.mkdir(parents=True)
            post_checkout_file = hooks_path / "post-checkout"

            with open(post_checkout_file, "w") as fh:
                fh.write("Existing file contents\n")

            self.call_command("install", temp_dir_name)

            with open(post_checkout_file, "r") as fh:
                contents = fh.read()
                # Original content is still there.
                self.assertTrue("Existing file contents" in contents)

                # And content has been appended.
                self.assertTrue("START django_migrant" in contents)

    @mock.patch("django_migrant.management.commands.migrant.stage_one")
    def test_migrate_stage_one(self, mock_stage_one):
        out, err = self.call_command("migrate")
        self.assertEqual(err, "")

        mock_stage_one.assert_called_once()

    @mock.patch.dict(os.environ, {"DJANGO_MIGRANT_STAGE": "TWO"})
    @mock.patch("django_migrant.management.commands.migrant.stage_two")
    def test_migrate_stage_two(self, mock_stage_two):
        out, err = self.call_command("migrate")
        self.assertEqual(err, "")

        mock_stage_two.assert_called_once()

    @mock.patch.dict(os.environ, {"DJANGO_MIGRANT_STAGE": "THREE"})
    @mock.patch("django_migrant.management.commands.migrant.stage_three")
    def test_migrate_stage_three(self, mock_stage_three):
        out, err = self.call_command("migrate")
        self.assertEqual(err, "")

        mock_stage_three.assert_called_once()
        mock_stage_three.assert_called_once()
