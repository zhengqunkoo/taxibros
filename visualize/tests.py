from django.test import TestCase
from django.background_task import Task

# Create your tests here.
class VisualizeIndexViewTests(TestCase):
    def test_no_data(self):
        """If no data exists (i.e. if server starts after a period of lull), an appropriate message is displayed
        """
        response = self.client.get(reverse('visualize:index'))
        self.assertEqual(response.status_code,200)
        self.assertContains(response,"No data is available, please wait a moment.")
        self.assertQuerysestEqual(response.context['coordinates'],[])
    def test_no_daemon(self):
        """If daemon is not running, an appropriate error message is displayed"""
        response = self.client.get(reverse('visualize:index'))
        self.assertEqual(response.status_code,200)
        self.assertContains(response,"Im sorry. The service appears to be experiencing a malfunction.")
        self.assertQuerysetEqual(Tasks.objects.all(),[])
