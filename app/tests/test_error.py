from unittest.mock import patch
from django.core.management import call_command
from app.tests.base import BaseTestCase
from app.parsers.ted import TEDWorker
from app.parsers.ungm import UNGMWorker


class UpdateErrorTestCase(BaseTestCase):

    @patch.object(
        TEDWorker, 'ftp_download_latest_archives',
        side_effect=Exception('Test error')
    )
    @patch('app.notifications.send_error_email')
    def test_ted_update_error(self, send_error_email, _):
        with self.assertRaises(Exception):
            call_command('update_ted')
        send_error_email.assert_called_once_with('Test error')

    @patch.object(
        UNGMWorker, 'parse_latest_notices',
        side_effect=Exception('Test error')
    )
    @patch('app.notifications.send_error_email')
    def test_ungm_update_error(self, send_error_email, _):
        with self.assertRaises(Exception):
            call_command('update_ungm', days_ago=1)
        send_error_email.assert_called_once_with('Test error')
