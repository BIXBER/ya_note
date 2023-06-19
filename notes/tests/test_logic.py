from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    NOTE_TEXT = 'Текст заметки'

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add')
        cls.success_url = reverse('notes:success')
        cls.user = User.objects.create(username='authorized_user')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {
            'title': 'Название заметки',
            'text': cls.NOTE_TEXT,
        }

    def test_anonymous_user_cant_add_note(self):
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        self.auth_client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)


class TestNoteEditDelete(TestCase):
    NOTE_TITLE = 'Название заметки'
    NEW_NOTE_TITLE = 'Новое название заметки'
    NOTE_TEXT = 'Текст заметки'
    NEW_NOTE_TEXT = 'Новый текст заметки'
    NOTE_SLUG = 'note_slug'
    NEW_NOTE_SLUG = 'new_note_slug'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор заметки')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.user = User.objects.create(username='Другой пользователь')
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug=cls.NOTE_SLUG,
            author=cls.author,
        )
        cls.note_url = reverse('notes:detail', kwargs={'slug': cls.note.slug})
        cls.edit_url = reverse('notes:edit', kwargs={'slug': cls.note.slug})
        cls.delete_url = reverse(
            'notes:delete',
            kwargs={'slug': cls.note.slug}
        )
        cls.form_data = {
            'title': cls.NEW_NOTE_TITLE,
            'text': cls.NEW_NOTE_TEXT,
            'slug': cls.NEW_NOTE_SLUG,
        }

    def test_author_can_delete_note(self):
        self.author_client.delete(self.delete_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        response = self.user_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        self.author_client.post(self.edit_url, data=self.form_data)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)
        self.assertEqual(self.note.slug, self.NEW_NOTE_SLUG)

    def test_user_cant_edit_note_of_another_user(self):
        response = self.user_client.post(self.edit_url, data=self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NOTE_TITLE)
        self.assertEqual(self.note.text, self.NOTE_TEXT)
        self.assertEqual(self.note.slug, self.NOTE_SLUG)


class TestExistingSlug(TestCase):
    NOTE_TITLE = 'Название заметки'
    NOTE_TEXT = 'Текст заметки'
    SLUG = 'notion'

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add')
        cls.user = User.objects.create(username='authorized_user')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            slug=cls.SLUG,
            author=cls.user,
        )
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'slug': cls.SLUG,
            'author': cls.user,
        }

    def test_user_cant_create_existing_slug(self):
        response = self.auth_client.post(self.url, data=self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=self.SLUG + WARNING
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
