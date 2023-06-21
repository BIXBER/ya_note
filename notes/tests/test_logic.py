from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    NOTE_TITLE = 'Название заметки'
    NOTE_TEXT = 'Текст заметки'
    SLUG = 'notion'

    @classmethod
    def setUpTestData(cls):
        cls.add_url = reverse('notes:add')
        cls.success_url = reverse('notes:success')
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
            'slug': cls.SLUG
        }
        cls.COUNT_NOTES = Note.objects.count()

    def test_availability_add_note_for_different_users(self):
        user_notes = (
            (self.client, self.COUNT_NOTES),
            (self.auth_client, self.COUNT_NOTES + 1)
        )
        for item in user_notes:
            user, expected_count_notes = item
            with self.subTest(user=user):
                self.form_data['slug'] += '_unique'
                user.post(self.add_url, data=self.form_data)
                result_count_notes = Note.objects.count()
                self.assertEqual(result_count_notes, expected_count_notes)

    def test_empty_slug(self):
        expected_count_notes = self.COUNT_NOTES + 1
        self.form_data.pop('slug')
        response = self.auth_client.post(self.add_url, data=self.form_data)
        self.assertRedirects(response, self.success_url)
        result_count_notes = Note.objects.count()
        self.assertEqual(result_count_notes, expected_count_notes)
        new_note = Note.objects.last()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)

    def test_user_cant_create_note_with_existing_slug(self):
        response = self.auth_client.post(self.add_url, data=self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=(self.SLUG + WARNING)
        )
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
