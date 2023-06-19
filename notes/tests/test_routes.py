from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note


User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='admin')
        cls.reader = User.objects.create(username='user')
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст',
            author=cls.author)

    def test_availability_pages(self):
        urls = (
            ('notes:home', None),
            ('users:login', None),
            ('users:logout', None),
            ('users:signup', None),
        )
        for item in urls:
            name, args = item
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_note(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for item in users_statuses:
            user, status = item
            self.client.force_login(user)
            for name in ('notes:detail', 'notes:edit', 'notes:delete'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, kwargs={'slug': self.note.slug})
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_redirect_for_anonimous_client(self):
        login_url = reverse('users:login')
        for name in ('notes:detail', 'notes:edit', 'notes:delete'):
            with self.subTest(name=name):
                url = reverse(name, kwargs={'slug': self.note.slug})
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
