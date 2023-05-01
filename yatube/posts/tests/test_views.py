from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='volodia',
            password='12345'
        )
        cls.group = Group.objects.create(
            title='Тест группа',
            slug='test-slug',
            description='Тест описание'
        )
        cls.post = Post.objects.create(
            text='Тест текст',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """Проверка namespace:name и tamplate_name"""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': self.user}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:group_list',
                                                 kwargs={'slug': 'test-slug'}))
        self.assertEqual(response.context['group'].title, 'Тест группа')
        self.assertEqual(response.context['group'].slug, 'test-slug')
        self.assertEqual(
            response.context['group'].description, 'Тест описание'
        )
        self.assertEqual(response.context['group'], self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username': self.user}
        ))
        post_count = self.post.author.posts.count()
        self.assertEqual(response.context['post_count'], post_count)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}
        ))
        post_count = self.post.author.posts.count()
        post = Post.objects.filter(id=self.post.pk)
        self.assertEqual(response.context['post_count'], post_count)
        self.assertEqual(response.context['post'], *post)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}
        ))
        post = Post.objects.filter(id=self.post.pk)
        self.assertTrue(response.context['is_edit'])
        self.assertEqual(response.context['post'], *post)

        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_group_show_in_pages(self):
        """Группа ожидаемо отображается в index, group_list, profile
        при создании поста.
        """
        group_test = Post.objects.filter(group=self.post.group).last()
        templates_page_group = {
            reverse('posts:index'): group_test,
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): group_test,
            reverse(
                'posts:profile', kwargs={'username': self.user}
            ): group_test
        }
        for value, expected in templates_page_group.items():
            with self.subTest(value=value):
                response = self.guest_client.get(value)
                form_field = response.context['page_obj']
                self.assertIn(expected, form_field)

    def test_group_correct_show_in_expect_page(self):
        """Пост не попал в группу, для которой не был предназначен"""
        group_new = Group.objects.create(
            title='Тест группа 2',
            slug='test2-slug',
            description='Тест описание 2'
        )
        templates_page_group = {
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            ): group_new,
        }
        for value, expected in templates_page_group.items():
            with self.subTest(value=value):
                response = self.guest_client.get(value)
                form_field = response.context['page_obj']
                self.assertNotIn(expected, form_field)


class PaginatorViewsTest(TestCase):
    NUMBER_OF_CREATE_TEST_POSTS = 13
    NUMBER_OF_TEST_POSTS_ON_FIRST_PAGE = 10
    NUMBER_OF_TEST_POSTS_ON_SECOND_PAGE = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='volodia',
            password='12345'
        )
        cls.group = Group.objects.create(
            title='Тест группа',
            slug='test-slug',
            description='Тест описание'
        )
        bulk_list = []
        for i in range(cls.NUMBER_OF_CREATE_TEST_POSTS):
            bulk_list.append(Post(
                text=f'Тест текст + {i}',
                author=cls.user,
                group=cls.group
            ))
        Post.objects.bulk_create(bulk_list)

    def setUp(self):
        cache.clear()
        self.guest_client = Client()

    def test_index_page_contains_ten_records(self):
        """Проверка пагинатора страницы index, стр 1"""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(
            len(response.context['page_obj']),
            self.NUMBER_OF_TEST_POSTS_ON_FIRST_PAGE
        )

    def test_index_page_contains_three_records(self):
        """Проверка пагинатора страницы index, стр 2"""
        response = self.guest_client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(
            len(response.context['page_obj']),
            self.NUMBER_OF_TEST_POSTS_ON_SECOND_PAGE
        )

    def test_group_list_page_contains_ten_records(self):
        """Проверка пагинатора страницы group_list, стр 1"""
        response = self.guest_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'})
        )
        self.assertEqual(
            len(response.context['page_obj']),
            self.NUMBER_OF_TEST_POSTS_ON_FIRST_PAGE
        )

    def test_group_list_page_contains_three_records(self):
        """Проверка пагинатора страницы group_list, стр 2"""
        response = self.guest_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'}) + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']),
            self.NUMBER_OF_TEST_POSTS_ON_SECOND_PAGE
        )

    def test_profile_page_contains_ten_records(self):
        """Проверка пагинатора страницы profile, стр 1"""
        response = self.guest_client.get(reverse(
            'posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(
            len(response.context['page_obj']),
            self.NUMBER_OF_TEST_POSTS_ON_FIRST_PAGE
        )

    def test_profile_page_contains_three_records(self):
        """Проверка пагинатора страницы profile, стр 2"""
        response = self.guest_client.get(reverse(
            'posts:profile',
            kwargs={'username': self.user}) + '?page=2'
        )
        self.assertEqual(
            len(response.context['page_obj']),
            self.NUMBER_OF_TEST_POSTS_ON_SECOND_PAGE
        )
