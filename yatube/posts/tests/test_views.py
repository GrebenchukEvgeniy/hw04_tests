from datetime import datetime

from django import forms
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User
from posts.utils import NUM_OF_PUBLICATIONS


NUM_OF_PUBLICATIONS_2ND_PAGE: int = 3


class PostViewsTests(TestCase):
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
            pub_date=datetime.now(),
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_authorized_client = Client()
        self.author_authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{self.post.id}'}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': f'{self.post.id}'}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.author_authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.author_authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group
        post_text_0 = first_object.text
        post_pub_date_0 = first_object.pub_date
        self.assertEqual(post_author_0, self.user.username)
        self.assertEqual(post_group_0, self.group)
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_pub_date_0, self.post.pub_date)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.author_authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        self.assertEqual(response.context.get('group').slug, self.group.slug)
        self.assertEqual(
            response.context.get('group').title, self.group.title)
        self.assertEqual(
            response.context.get('group').description, self.group.description)
        self.assertEqual(
            response.context.get('page_obj')[0].author.username,
            self.user.username)
        self.assertEqual(
            response.context.get('page_obj')[0].group, self.group)
        self.assertEqual(
            response.context.get('page_obj')[0].text, self.post.text)
        self.assertEqual(
            response.context.get('page_obj')[0].pub_date,
            self.post.pub_date)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.author_authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.user.username})
        )
        self.assertEqual(response.context.get('author').username,
                         self.user.username)
        self.assertEqual(
            response.context.get('page_obj')[0].group, self.group)
        self.assertEqual(
            response.context.get('page_obj')[0].text, self.post.text)
        self.assertEqual(
            response.context.get('page_obj')[0].pub_date,
            self.post.pub_date)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.author_authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': f'{self.post.id}'})
        )
        self.assertEqual(
            response.context.get('post').id, int(f'{self.post.id}'))
        self.assertEqual(
            response.context.get('post').author.username, self.user.username)
        self.assertEqual(
            response.context.get('post').group, self.group)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(
            response.context.get('post').pub_date,
            self.post.pub_date)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.author_authorized_client.get(
            reverse('posts:post_create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author_authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': f'{self.post.id}'})
        )
        self.assertEqual(
            response.context.get('post').id, int(f'{self.post.id}'))
        self.assertEqual(
            response.context.get('post').author.username, self.user.username)
        self.assertEqual(
            response.context.get('post').group, self.group)
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(
            response.context.get('post').pub_date,
            self.post.pub_date)
        self.assertNotEqual(
            response.context.get('post').group, self.group_new)

    def test_new_post_is_not_in_group_new(self):
        """Тест проверки, что новый пост не в неправильной группе."""
        response = self.author_authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_new.slug}))
        self.assertEqual(len(response.context.get('page_obj').object_list), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Тестовое описание',
            slug='test-slug'
        )
        for i in range(NUM_OF_PUBLICATIONS + NUM_OF_PUBLICATIONS_2ND_PAGE):
            cls.post = Post.objects.create(
                author=cls.user,
                text=f'Тестовый пост {i}',
                pub_date=datetime.now(),
                group=cls.group
            )

    def test_first_page_contains_ten_records(self):
        templates_pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for page in templates_pages_names:
            response = self.client.get(page)
            self.assertEqual(
                len(response.context['page_obj']), NUM_OF_PUBLICATIONS)

    def test_second_page_contains_three_records(self):
        templates_pages_names = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for page in templates_pages_names:
            response = self.client.get(page + '?page=2')
            self.assertEqual(
                len(response.context['page_obj']),
                NUM_OF_PUBLICATIONS_2ND_PAGE)
