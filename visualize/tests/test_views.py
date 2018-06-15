from django.test import TestCase
from background_task.models import Task
from daemons.download import start_download
from django.urls import reverse

# Create your tests here.
class VisualizeIndexViewTests(TestCase):

    def test_no_data(self):
        """If no data exists (i.e. if server starts after a period of lull), an appropriate message is displayed
        """
        start_download()  # Runs daemon to escape first check
        response = self.client.get(reverse("visualize:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Data is still incomplete, please wait a few minutes before refreshing.",
        )
        Task.objects.all().delete()  # Deletes daemon

    def test_no_daemon(self):
        """If daemon is not running, an appropriate error message is displayed"""
        response = self.client.get(reverse("visualize:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "No daemons running. Please run server once with DAEMON_START=True.",
        )
