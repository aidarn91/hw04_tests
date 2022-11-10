from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='test_name')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='Проверка описания',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
            group=Group.objects.get(slug='test_slug'),
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self, *args, **kwargs):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostPagesTests.group.slug}):
                    'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostPagesTests.user.username}):
                    'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.post.id}):
                    'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTests.post.id}):
                    'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(post_author_0, 'test_name')
        self.assertEqual(post_group_0, 'test_group')

    def test_group_pages_show_correct_context(self):
        """Шаблон группы"""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test_slug'}))
        first_object = response.context['group']
        group_title_0 = first_object.title
        group_slug_0 = first_object.slug
        self.assertEqual(group_title_0, 'test_group')
        self.assertEqual(group_slug_0, 'test_slug')

    def test_post_another_group(self):
        """Пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertTrue(post_text_0, 'Тестовый текст')

    def test_new_post_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'test_name'}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        self.assertEqual(response.context['author'].username, 'test_name')
        self.assertEqual(post_text_0, 'Тестовый текст')

    def test_detail_page_show_correct_context(self):
        """Шаблон post_detail.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}))
        first_object = response.context['post']
        post_author_0 = first_object.author.username
        post_text_0 = first_object.text
        group_slug_0 = first_object.group.slug
        self.assertEqual(post_author_0, 'test_name')
        self.assertEqual(post_text_0, 'Тестовый текст')
        self.assertEqual(group_slug_0, 'test_slug')


class PostPaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_name1')
        cls.group = Group.objects.create(
            title="test_group1",
            slug='test_slug1',
            description='Тестовое описание1',
        )
        for post_number in range(13):
            cls.post = Post.objects.bulk_create([
                Post(
                    text=f'Тестовый текст {post_number}',
                    author=cls.user,
                    group=cls.group
                )])

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_posts(self):
        paginator_list = {
            'posts:index': reverse('posts:index'),
            'posts:group_list': reverse(
                'posts:group_list',
                kwargs={'slug': 'test_slug1'}),
            'posts:profile': reverse(
                'posts:profile', kwargs={'username': 'test_name1'}),
        }
        for template, reverse_name in paginator_list.items():
            response = self.guest_client.get(reverse_name)
            self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_ten_posts(self):
        paginator_list = {
            'posts:index': reverse('posts:index') + '?page=2',
            'posts:group_list': reverse(
                'posts:group_list',
                kwargs={'slug': 'test_slug1'}) + '?page=2',
            'posts:profile': reverse(
                'posts:profile',
                kwargs={'username': 'test_name1'}) + '?page=2',
        }
        for template, reverse_name in paginator_list.items():
            response = self.guest_client.get(reverse_name)
            self.assertEqual(len(response.context['page_obj']), 3)
