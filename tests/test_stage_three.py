import unittest
from unittest import mock

from django_nomad.management.commands import nomad


class TestStageThree(unittest.TestCase):

    @mock.patch("django_nomad.management.commands.nomad.call_command")
    def test_command_called(self, mock_call_command):

        nomad.stage_three()

        mock_call_command.assert_called_once()
        self.assertTrue(len(mock_call_command.call_args_list), 1)
        self.assertEqual(mock_call_command.call_args.args, ("migrate",))
