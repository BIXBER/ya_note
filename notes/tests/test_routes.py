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
        cls.url_note_args = (cls.note.slug,)

    def test_availability_pages(self):
        urls = (
            ('notes:home'),
            ('users:login'),
            ('users:logout'),
            ('users:signup'),
        )
        for name in urls:
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_note_for_different_users(self):
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

    def test_availability_pages_for_auth_user(self):
        for name in ('notes:add', 'notes:list', 'notes:success'):
            self.client.force_login(self.reader)
            with self.subTest(name=name):
                response = self.client.get(reverse(name))
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_user(self):
        login_url = reverse('users:login')
        slug_args = self.url_note_args
        urls = (
            ('notes:add', None),
            ('notes:list', None),
            ('notes:success', None),
            ('notes:detail', slug_args),
            ('notes:edit', slug_args),
            ('notes:delete', slug_args)
        )
        for item in urls:
            name, args = item
            with self.subTest(name=name, args=args):
                url = reverse(name, args=args)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
