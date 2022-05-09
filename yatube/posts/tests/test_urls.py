from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class GroupURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='auth2')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            pub_date='Тестовая дата',
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_authorized_client = Client()
        self.author_authorized_client.force_login(self.user)
        self.not_author_authorized_client = Client()
        self.not_author_authorized_client.force_login(self.user2)

    def test_url_exists_at_desired_location_guest_client(self):
        """Тестирование доступности страниц для неавторизованного пользователя
        и редиректов для неавторизованного."""
        templates_url_names = {
            '/': HTTPStatus.OK,
            '/group/test-slug/': HTTPStatus.OK,
            '/profile/auth/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.FOUND,
            '/unexating_page/': HTTPStatus.NOT_FOUND,
        }
        for template, status in templates_url_names.items():
            with self.subTest(status=status):
                response = self.guest_client.get(template)
                self.assertEqual(response.status_code, status)

    def test_url_exists_at_desired_location_not_author_authorized_client(self):
        """Тесты доступности страниц для
        авторизованного (не автора) пользователя."""
        templates_url_names = {
            f'/posts/{self.post.id}/edit/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.OK,
        }
        for template, status in templates_url_names.items():
            with self.subTest(status=status):
                response = self.not_author_authorized_client.get(template)
                self.assertEqual(response.status_code, status)

    def test_url_exists_at_desired_location_author_authorized_client(self):
        """Тесты доступности страницы /posts/post.id/edit/
        для авторизованного (автора) пользователя."""
        response = self.author_authorized_client.get(
            f'/posts/{self.post.id}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirect_anonymous(self):
        """Страница /create/ перенаправляет анонимного
        пользователя на страницу логина."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_post_edit_url_redirect_anonymous(self):
        """Страница /posts/post.id/edit/ перенаправляет анонимного
        пользователя на страницу логина."""
        response = self.guest_client.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_post_edit_url_redirect_not_author_authorized_client(self):
        """Страница /posts/post.id/edit/ перенаправляет
        не автора поста на страницу поста."""
        response = self.not_author_authorized_client.get(
            f'/posts/{self.post.id}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/posts/{self.post.id}/'
        )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/auth/': 'posts/profile.html',
            f'/posts/{self.post.id}/': 'posts/post_detail.html',
            f'/posts/{self.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_authorized_client.get(address)
                self.assertTemplateUsed(response, template)
