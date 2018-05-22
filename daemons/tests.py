from django.test import TestCase
from background_task.models import Task

# Create your tests here.
class DaemonRunningTests(TestCase):
    def test_single_running_daemon(self):
        """Ensures that daemon is running"""
        self.assertEqual(Task.objects.all().count(),1)
