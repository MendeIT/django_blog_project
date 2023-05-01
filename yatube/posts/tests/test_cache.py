from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post

User = get_user_model()


class CacheTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='volodia',
            password='12345'
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def tearDown(self):
        cache.clear()

    def test_cache(self):
        """Тест кеша главной страницы"""
        form_data = {
            'text': 'Создан тестовый пост'
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        response = self.authorized_client.get(reverse('posts:index'))
        first_post = response.content

        Post.objects.filter(text=form_data['text']).delete()

        response_second = self.authorized_client.get(reverse('posts:index'))
        first_post_after_del = response_second.content

        self.assertEqual(first_post, first_post_after_del)

        cache.clear()

        response_after_del = self.authorized_client.get(reverse('posts:index'))
        first_post_after_del_cache = response_after_del.content

        self.assertNotEqual(first_post_after_del, first_post_after_del_cache)
