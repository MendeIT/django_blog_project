from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Post

User = get_user_model()


class FollowersTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='Автор поста',
            password='12345'
        )
        cls.post = Post.objects.create(
            text='Пост',
            author=cls.user
        )
        cls.subscriber = User.objects.create_user(
            username='Подписчик',
            password='12345'
        )
        cls.url = {
            'follow_index': reverse('posts:follow_index'),
            'profile_follow': reverse(
                'posts:profile_follow',
                kwargs={'username': cls.user}
            ),
            'profile_unfollow': reverse(
                'posts:profile_unfollow',
                kwargs={'username': cls.user}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': cls.user}
            ),
            'post_create': reverse('posts:post_create')
        }

    def setUp(self):
        cache.clear()
        self.authorized_subscriber = Client()
        self.authorized_subscriber.force_login(self.subscriber)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user)

    def test_pages_follow_available(self):
        """Страницы follow_index, profile_follow, unfollow доступны."""
        response = self.authorized_subscriber.get(self.url['follow_index'])
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_subscriber.get(self.url['profile_follow'])
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.authorized_subscriber.get(self.url['profile_unfollow'])
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_path_correct_template_used(self):
        """Шаблон follow.html соответствует ожидаемому пути."""
        templates = {
            self.url['follow_index']: 'posts/follow.html',
        }
        for reverse_name, template in templates.items():
            with self.subTest(template=template):
                response = self.authorized_subscriber.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_subscribe_redirect_to_profile(self):
        """При подписке/отписке пользователь перенаправляется
        на страницу profile автора
        """
        response = self.authorized_subscriber.get(self.url['profile_follow'])
        self.assertRedirects(response, self.url['profile'])

        response = self.authorized_subscriber.get(self.url['profile_unfollow'])
        self.assertRedirects(response, self.url['profile'])

    def test_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок.
        """
        response = self.authorized_subscriber.get(self.url['follow_index'])
        count_posts = len(response.context['page_obj'])
        self.assertEqual(count_posts, 0)

        self.authorized_subscriber.get(self.url['profile_follow'])

        response_after_subscribe = self.authorized_subscriber.get(
            self.url['follow_index']
        )
        count_posts_after_subscribe = len(
            response_after_subscribe.context['page_obj']
        )
        self.assertEqual(count_posts_after_subscribe, 1)
        self.assertNotEqual(count_posts, count_posts_after_subscribe)

        self.authorized_subscriber.get(self.url['profile_unfollow'])
        response_after_unsubscribe = self.authorized_subscriber.get(
            self.url['follow_index']
        )
        count_posts_after_unsubscribe = len(
            response_after_unsubscribe.context['page_obj']
        )
        self.assertEqual(count_posts_after_unsubscribe, 0)

    def test_show_new_post_in_page_subscriber(self):
        """Новая запись автора появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан.
        """
        self.authorized_subscriber.get(self.url['profile_follow'])
        response = self.authorized_subscriber.get(self.url['follow_index'])
        count_posts = len(response.context['page_obj'])

        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый пост'
        }
        self.authorized_author.post(
            self.url['post_create'],
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)

        reresponse = self.authorized_subscriber.get(self.url['follow_index'])
        count_posts_after_add_post = len(reresponse.context['page_obj'])
        self.assertEqual(count_posts_after_add_post, count_posts + 1)

        post_2 = reresponse.context['page_obj'][0]
        self.assertEqual(post_2.text, form_data['text'])

        self.authorized_subscriber.get(self.url['profile_unfollow'])

        new_response = self.authorized_subscriber.get(self.url['follow_index'])
        count_posts_after_unsubscribe = len(new_response.context['page_obj'])
        self.assertEqual(count_posts_after_unsubscribe, 0)
        self.assertEqual(len(Post.objects.all()), 2)
