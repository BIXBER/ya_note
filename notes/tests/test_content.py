from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase


User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='author')
        cls.add_url = reverse('notes:add')

    def test_authorized_client_has_form(self):
        self.client.force_login(self.author)
        response = self.client.get(self.add_url)
        self.assertIn('form', response.context)
