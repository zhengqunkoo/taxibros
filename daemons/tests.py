from django.test import TestCase
from django.background_task import Task

# Create your tests here.
class DaemonRunningTests(TestCase):
    def test_single_running_daemon(self):
        """Ensures that daemon is running"""
        self.assertEqual(Tasks.objects.all().count(),1)
