import json
import unittest
from unittest import mock

from django.db.migrations.graph import Node

from django_migrant.management.commands import migrant


class TestStageTwo(unittest.TestCase):

    @mock.patch("django_migrant.management.commands.migrant.subprocess", mock.MagicMock())
    @mock.patch("django_migrant.management.commands.migrant.Path", mock.MagicMock())
    @mock.patch("django_migrant.management.commands.migrant.call_command")
    @mock.patch("django_migrant.management.commands.migrant.MigrationLoader")
    def test_migrate_to_zero(self, mock_loader, mock_call_command):
        # The give node 0001_initial has no parent, so we migrate to the
        # "zero" migration of that app.
        n1 = Node(("polls", "0001_initial"))
        mock_loader.return_value.graph.node_map = {n1.key: n1}
        file_contents = json.dumps(
            [
                ["polls", "0001_initial"],
            ]
        )
        with mock.patch(
            "builtins.open", mock.mock_open(read_data=file_contents)
        ) as mock_open:
            migrant.stage_two()
        handle = mock_open()
        handle.read.assert_called_once()

        mock_call_command.assert_called_once()
        self.assertTrue(len(mock_call_command.call_args_list), 1)
        self.assertEqual(mock_call_command.call_args.args, ("migrate", "polls", "zero"))

    @mock.patch("django_migrant.management.commands.migrant.subprocess", mock.MagicMock())
    @mock.patch("django_migrant.management.commands.migrant.Path", mock.MagicMock())
    @mock.patch("django_migrant.management.commands.migrant.call_command")
    @mock.patch("django_migrant.management.commands.migrant.MigrationLoader")
    def test_migrate_to_parent(self, mock_loader, mock_call_command):
        # To reverse 0002 we migrate to 0001.

        n1 = Node(("polls", "0001_initial"))
        n2 = Node(("polls", "0002_alter_question_question_text"))
        n2.add_parent(n1)
        mock_loader.return_value.graph.node_map = {n1.key: n1, n2.key: n2}
        file_contents = json.dumps([["polls", "0002_alter_question_question_text"]])
        with mock.patch(
            "builtins.open", mock.mock_open(read_data=file_contents)
        ) as mock_open:
            migrant.stage_two()
        handle = mock_open()
        handle.read.assert_called_once()

        mock_call_command.assert_called_once()
        self.assertTrue(len(mock_call_command.call_args_list), 1)
        self.assertEqual(
            mock_call_command.call_args.args, ("migrate", "polls", "0001_initial")
        )

    @mock.patch("django_migrant.management.commands.migrant.subprocess", mock.MagicMock())
    @mock.patch("django_migrant.management.commands.migrant.Path", mock.MagicMock())
    @mock.patch("django_migrant.management.commands.migrant.call_command")
    @mock.patch("django_migrant.management.commands.migrant.MigrationLoader")
    def test_migrate_to_single_ancestor(self, mock_loader, mock_call_command):
        # The provided file gives a list of migrations in the same app. Make sure
        # we only migrate to one of them.

        n1 = Node(("polls", "0001_initial"))
        n2 = Node(("polls", "0002_alter_question_question_text"))
        n2.add_parent(n1)
        n3 = Node(("polls", "0003_alter_title"))
        n3.add_parent(n2)
        n4 = Node(("polls", "0004_alter_description"))
        n4.add_parent(n3)
        mock_loader.return_value.graph.node_map = {
            n1.key: n1,
            n2.key: n2,
            n3.key: n3,
            n4.key: n4,
        }
        file_contents = json.dumps(
            [
                ["polls", "0002_alter_question_question_text"],
                ["polls", "0003_alter_title"],
                ["polls", "0004_alter_description"],
            ]
        )
        with mock.patch(
            "builtins.open", mock.mock_open(read_data=file_contents)
        ) as mock_open:
            migrant.stage_two()
        handle = mock_open()
        handle.read.assert_called_once()

        mock_call_command.assert_called_once()
        self.assertTrue(len(mock_call_command.call_args_list), 1)
        self.assertEqual(
            mock_call_command.call_args.args, ("migrate", "polls", "0001_initial")
        )
