from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase, Client

from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='author')
        cls.reader = User.objects.create(username='reader')
        cls.author_client = Client()
        cls.reader_client = Client()
        cls.author_client.force_login(cls.author)
        cls.reader_client.force_login(cls.reader)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note_slug',
            author=cls.author,
        )
        cls.add_url = reverse('notes:add')
        cls.list_url = reverse('notes:list')
        cls.url_note_args = (cls.note.slug,)

    def test_notes_list_for_different_users(self):
        user_forms = (
            (self.author_client, True),
            (self.reader_client, False)
        )
        for item in user_forms:
            user, note_in_list = item
            with self.subTest(user=user, is_display=note_in_list):
                response = user.get(self.list_url)
                object_list = response.context['object_list']
                self.assertIs((self.note in object_list), note_in_list)

    def test_pages_contains_form(self):
        slug_args = self.url_note_args
        urls = (
            ('notes:add', None),
            ('notes:edit', slug_args),
        )
        for item in urls:
            name, args = item
            with self.subTest(name=name):
                url = reverse(name, args=args)
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
