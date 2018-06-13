from django.test import TestCase
from background_task.models import Task
from daemons.download import start_download

# Create your tests here.
class DaemonRunningTests(TestCase):
    def test_single_running_daemon(self):
        """Ensures that daemon is runs a single instance of task"""
        start_download()  # Runs daemon to escape first check
        self.assertEqual(Task.objects.all().count(), 1)
        Task.objects.all().delete()
