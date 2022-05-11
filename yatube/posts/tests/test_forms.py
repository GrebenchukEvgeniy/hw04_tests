import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug'
        )
        cls.group_new = Group.objects.create(
            title='Тестовый заголовок новый',
            description='Тестовое описание новое',
            slug='test-slug-new'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            pub_date='Тестовая дата',
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author_authorized_client = Client()
        self.author_authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        bunch_posts_old = set(Post.objects.all())
        form_data = {
            'group': self.group.id,
            'text': 'Проверка поста',
        }
        response = self.author_authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': self.user.username})
        )
        bunch_posts_new = set(Post.objects.all())
        diff_bunches = bunch_posts_new - bunch_posts_old
        self.assertEqual(len(diff_bunches), 1)
        post_check = diff_bunches.pop()
        self.assertEqual(form_data['text'], post_check.text)

    def test_edit_post(self):
        """Проверка формы редактирования поста и изменение
        его в базе данных."""
        bunch_posts_old = set(Post.objects.all())
        form_data = {
            'group': self.group.id,
            'text': 'Тестовое редактирование',
        }
        response = self.author_authorized_client.post(reverse(
            'posts:post_edit', kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': f'{self.post.id}'})
        )
        bunch_posts_new = set(Post.objects.all())
        diff_bunches = bunch_posts_new - bunch_posts_old
        self.assertEqual(len(diff_bunches), 0)
        post_check = bunch_posts_new.pop()
        self.assertEqual(form_data['text'], post_check.text)


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()

    def test_title_label(self):
        """Тестирование labels в форме PostForm."""
        text_label = PostFormTests.form.fields['text'].label
        group_label = PostFormTests.form.fields['group'].label
        self.assertEqual(text_label, 'Текст поста:')
        self.assertEqual(group_label, 'Группа:')

    def test_title_help_text(self):
        """Тестирование help_text в форме PostForm."""
        text_help_text = PostFormTests.form.fields['text'].help_text
        group_help_text = PostFormTests.form.fields['group'].help_text
        self.assertEqual(text_help_text, 'Текст нового поста')
        self.assertEqual(
            group_help_text, 'Группа, к которой будет относиться пост'
        )
