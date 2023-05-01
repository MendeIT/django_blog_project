import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
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
        cls.form = PostForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        path = [
            reverse('posts:post_create'),
            reverse('posts:profile', kwargs={'username': self.user})
        ]
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Создан новый пост',
            'group': self.post.group.pk,
        }
        response = self.authorized_client.post(
            path[0],
            data=form_data,
            follow=True
        )
        new_post = Post.objects.latest('id')
        self.assertRedirects(response, path[1])
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(self.user, new_post.author)
        self.assertEqual(self.group, new_post.group)

    def test_edit_post(self):
        """Отредактированный пост отображается корректно."""
        path = [
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}),
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        ]
        posts_count = Post.objects.count()
        old_text_post = self.post.text
        new_group = Group.objects.create(
            title='Тест группа 2',
            slug='test-slug-slug',
            description='Тест описание 2'
        )
        form_data = {
            'text': 'Изменяемый текст',
            'group': new_group.pk,
        }
        response = self.authorized_client.post(
            path[0],
            data=form_data,
            follow=True
        )
        old_group_response = self.authorized_client.get(path[2])
        new_group_response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': new_group.slug})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(response, path[1])
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(Post.objects.filter(text=form_data['text']).exists())
        self.assertTrue(Post.objects.filter(group=form_data['group']).exists())
        self.assertNotEqual(response, old_text_post)
        self.assertEqual(
            old_group_response.context['page_obj'].paginator.count, 0
        )
        self.assertEqual(
            new_group_response.context['page_obj'].paginator.count, 1
        )

    def test_title_help_text(self):
        """help_text корректно отображается."""
        text_help_text = PostCreateFormTests.form.fields['text'].help_text
        group_help_text = PostCreateFormTests.form.fields['group'].help_text
        self.assertEqual(text_help_text, 'Введите текст поста')
        self.assertEqual(
            group_help_text, 'Группа, к которой будет относиться пост'
        )


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TestViewImage(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='Atom',
            password='12345'
        )
        cls.group = Group.objects.create(
            title='Тест группа',
            slug='test-slug',
            description='Тест описание'
        )
        cls.post = Post.objects.create(
            text='Тест текст',
            group=cls.group,
            author=cls.user,
            image=None
        )
        cls.form = PostForm()
        cls.url = {
            'index': reverse('posts:index'),
            'profile': reverse('posts:profile', kwargs={'username': cls.user}),
            'group_list': reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}
            ),
            'post_detail': reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.pk}
            ),
            'post_create': reverse('posts:post_create')
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_correct_show_image_in_pages(self):
        """Картинка корректно отображается на страницах
        (index, profile, group_list, post_detail)
        """
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'group': self.group.pk,
            'text': 'С картинкой',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            self.url['post_create'],
            data=form_data,
            follow=True
        )
        new_post = Post.objects.latest(field_name='pub_date')

        response_index = self.client.get(self.url['index'])
        first_post_index = response_index.context['page_obj'][0]

        response_profile = self.client.get(self.url['profile'])
        first_post_profile = response_profile.context['page_obj'][0]

        response_group_list = self.client.get(self.url['group_list'])
        first_post_group_list = response_group_list.context['page_obj'][0]

        response_post_detail = self.client.get(reverse(
            'posts:post_detail', kwargs={'post_id': new_post.pk}
        ))
        post_detail = response_post_detail.context['post']

        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertRedirects(response, self.url['profile'])
        self.assertTrue(Post.objects.filter(image=new_post.image).exists())
        self.assertEqual(new_post.image, first_post_index.image)
        self.assertEqual(new_post.image, first_post_profile.image)
        self.assertEqual(new_post.image, first_post_group_list.image)
        self.assertEqual(new_post.image, post_detail.image)


class СommetCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='Neo',
            password='12345'
        )
        cls.post = Post.objects.create(
            text='Тест текст',
            author=cls.user
        )
        cls.comment = cls.post.comments.create(
            text='Первый коммент',
            author=cls.user
        )
        cls.form = CommentForm()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment_add_only_authorized_user(self):
        """Комментировать может только авторизованный пользователь"""
        comment_count = self.post.comments.count()
        form_data = {
            'text': 'Второй коммент'
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': self.post.id}
            ),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}
        ))
        self.assertEqual(self.post.comments.count(), comment_count + 1)
        self.assertTrue(
            self.post.comments.filter(text=form_data['text']).exists()
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
