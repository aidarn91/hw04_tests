from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Group, Post
from posts.forms import PostForm

User = get_user_model()


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_user')
        cls.group = Group.objects.create(
            title='test_group',
            slug='test_slug',
            description='Тестовое описание'
        )

        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.author,
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.author)
        cls.form = PostForm()

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text='Тестовый текст',
            group=self.group.pk).exists())

    def test_edit_post(self):
        form_data = {
            'text': 'Новый текст поста',
            'group': self.group.pk,
        }
        self.authorized_client.post(reverse(
            'posts:post_edit',
            kwargs={'post_id': self.post.id},
        ), data=form_data)
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id},
        ))
        self.assertEqual(response.context['post'].text, 'Новый текст поста')
        self.assertTrue(Post.objects.filter(
            text='Новый текст поста',
            group=self.group.pk,
        ).exists())
