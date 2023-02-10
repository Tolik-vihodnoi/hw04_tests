import shutil
import tempfile
from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Page
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, Comment, Follow


TEMP_MEDIA_ROOT = tempfile.mktemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_0 = User.objects.create(username='FatWhiteFamily')
        cls.user_1 = User.objects.create(username='Adept')
        cls.group_0 = Group.objects.create(
            title='Тестовая группа 0',
            slug='test_group_0',
            description='Тестовое описание 0'
        )
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_group_1',
            description='Тестовое описание 1'
        )
        img_data = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.jpg',
            content=img_data,
            content_type='image/jpeg'
        )
        cls.post = Post.objects.create(
            group=cls.group_0,
            text='text of test article',
            author=cls.user_0,
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            post=PostViewTest.post,
            author=PostViewTest.user_0,
            text='test comment actually'
        )
        cls.follow = Follow.objects.create(
            user=cls.user_1,
            author=cls.user_0
        )
        cls.form_fields_list = {
            'group': forms.ChoiceField,
            'text': forms.CharField,
        }
        cls.follow_url = 'posts:follow_index'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.auth_client_0 = Client()
        self.auth_client_0.force_login(PostViewTest.user_0)
        self.auth_client_1 = Client()
        self.auth_client_1.force_login(PostViewTest.user_1)

    def check_post(self, context, is_page=True):
        if is_page:
            ext_post = context.get('page_obj')
            self.assertIsInstance(ext_post, Page)
            if not ext_post:
                raise AssertionError('It seems like the page_obj is empty.')
            post = ext_post[0]
        else:
            post = context.get('post')
        self.assertIsInstance(post, Post)
        self.assertEqual(post.text, PostViewTest.post.text)
        self.assertEqual(post.author, PostViewTest.post.author)
        self.assertEqual(post.group, PostViewTest.post.group)
        self.assertEqual(post.pub_date, PostViewTest.post.pub_date)
        upload_dir = post._meta.get_field('image').upload_to
        self.assertEqual(
            post.image, f'{upload_dir}{PostViewTest.uploaded.name}'
        )

    def test_pages_use_correct_templates(self):
        """Проверяет, что namespace:name вызывает корректные шаблоны"""
        url_name_dict = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', args=(PostViewTest.group_0.slug,)
                    ): 'posts/group_list.html',
            reverse('posts:profile', args=(PostViewTest.user_0,)
                    ): 'posts/profile.html',
            reverse('posts:post_detail', args=(PostViewTest.post.id,)
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit', args=(PostViewTest.post.id,)
                    ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for url_name, templ in url_name_dict.items():
            with self.subTest(url_name=url_name):
                response = self.auth_client_0.get(url_name)
                self.assertTemplateUsed(response, templ)

    def test_index_page_context(self):
        """Проверяет коррекстность переданного контекста
         на главной странице."""
        context = self.auth_client_0.get(reverse('posts:index')).context
        self.check_post(context)

    def test_group_list_page_context(self):
        """Проверяет коррекстность переданного контекста на странице группы."""
        context = self.auth_client_0.get(
            reverse('posts:group_list', args=(PostViewTest.group_0.slug,))
        ).context
        self.check_post(context)
        self.assertEqual(context.get('group'), PostViewTest.group_0)

    def test_profile_page_context(self):
        """Проверяет коррекстность переданного контекста
        на странице профайла."""
        context = self.auth_client_0.get(
            reverse('posts:profile', args=(PostViewTest.user_0.username,))
        ).context
        self.check_post(context)
        self.assertEqual(context.get('posts_owner'), PostViewTest.user_0)

    def test_post_detail_page_context(self):
        """Проверяет коррекстность переданного контекста
        на странице деталей поста."""
        context = self.auth_client_0.get(
            reverse('posts:post_detail', args=(PostViewTest.post.pk,))
        ).context
        self.check_post(context, is_page=False)
        self.assertIn('comments', context)
        comments = context['comments']
        self.assertEqual(len(comments), 1)
        comment = comments[0]
        self.assertIsInstance(comment, Comment)
        self.assertEqual(comment.text, PostViewTest.comment.text)
        self.assertEqual(comment.author, PostViewTest.comment.author)
        self.assertEqual(comment.post, PostViewTest.comment.post)

    def test_tested_post_not_exist(self):
        url_list = [
            reverse('posts:group_list', args=(PostViewTest.group_1.slug,)),
            reverse('posts:profile', args=(PostViewTest.user_1,)),
        ]
        for url in url_list:
            with self.subTest(url=url):
                page_obj = self.auth_client_0.get(url).context.get(
                    'page_obj', [])
                self.assertNotIn(PostViewTest.post, page_obj)

    def test_form_creating_post(self):
        """Проверяет форму создания поста на коррекстность типов полей."""
        response = self.auth_client_0.get(reverse('posts:post_create'))
        for field, form_field in PostViewTest.form_fields_list.items():
            with self.subTest(field=field):
                form_obj = response.context.get('form')
                self.assertIsInstance(form_obj, PostForm)
                field_value = form_obj.fields.get(field)
                self.assertIsInstance(field_value, form_field)

    def test_form_editing_post(self):
        """Проверяет форму редактирования поста, отфильтрованного по id,
        на коррекстность типов полей."""
        response = self.auth_client_0.get(
            reverse('posts:post_edit', args=(PostViewTest.post.pk,))
        )
        for field, form_field in PostViewTest.form_fields_list.items():
            with self.subTest(field=field):
                form_obj = response.context.get('form')
                self.assertIsInstance(form_obj, PostForm)
                field_value = form_obj.fields.get(field)
                self.assertIsInstance(field_value, form_field)

    def test_is_index_page_data_cached(self):
        """Проверяет кэшироване главное страницы."""
        resp_before = self.auth_client_0.get(reverse('posts:index'))
        Post.objects.all().delete()
        resp_after = self.auth_client_0.get(reverse('posts:index'))
        cache.clear()
        resp_cleared_cache = self.auth_client_0.get(reverse('posts:index'))
        self.assertEqual(resp_before.content, resp_after.content)
        self.assertNotEqual(resp_before.content, resp_cleared_cache.content)

    def test_can_auth_user_subscribe(self):
        """Проверяет может ли подписаться авторизованный пользователь."""
        Follow.objects.all().delete()
        for _ in range(2):
            self.auth_client_1.get(reverse(
                'posts:profile_follow',
                args=(PostViewTest.user_0.username,)
            ))
            self.assertEqual(Follow.objects.count(), 1)

    def test_can_auth_user__unsubscribe(self):
        """Проверяет может ли отписаться авторизованный пользователь."""
        self.assertEqual(Follow.objects.count(), 1)
        self.auth_client_1.get(reverse(
            'posts:profile_unfollow',
            args=(PostViewTest.user_0.username,)
        ))
        self.assertEqual(Follow.objects.count(), 0)

    def test_follow_page_has_post(self):
        """Проверяет что пост появился на странице подписок."""
        context = self.auth_client_1.get(
            reverse(PostViewTest.follow_url)).context
        self.check_post(context)

    def test_follow_page_has_not_post(self):
        """Проверяет что пост не появился на странице подписок."""
        context = self.auth_client_0.get(
            reverse(PostViewTest.follow_url)).context
        with self.assertRaisesMessage(
                AssertionError, 'It seems like the page_obj is empty.'):
            self.check_post(context)


class PaginatorTest(TestCase):

    PLUS_POSTS: int = 3

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='FatWhiteFamily')
        cls.group_0 = Group.objects.create(
            title='Тестовая группа 0',
            slug='test_group_0',
            description='Тестовое описание 0'
        )
        cls.group_1 = Group.objects.create(
            title='Тестовая группа 1',
            slug='test_group_1',
            description='Тестовое описание 1'
        )
        Post.objects.bulk_create(
            [Post(group=cls.group_0, text=f'text number {i}', author=cls.user)
             for i in range(settings.NUM_OF_POSTS + PaginatorTest.PLUS_POSTS)]
        )
        cls.urls_to_count = [
            reverse('posts:index'),
            reverse('posts:group_list', args=(PaginatorTest.group_0.slug,)),
            reverse('posts:profile', args=(PaginatorTest.user.username,)),
        ]

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(PaginatorTest.user)

    def test_paginator(self):
        """Проверяет пагинатор на соответствие назначенному кол-ву объектов
        на первой странице и второй (подразумевается последней)."""
        for url_name in PaginatorTest.urls_to_count:
            with self.subTest(url_name=url_name):
                resp_1_page = self.auth_client.get(url_name)
                resp_2_page = self.auth_client.get(url_name, {'page': 2})
                len_1page_posts = len(resp_1_page.context.get('page_obj'))
                len_2page_posts = len(resp_2_page.context.get('page_obj'))
                self.assertEqual(len_1page_posts, settings.NUM_OF_POSTS)
                self.assertEqual(len_2page_posts, PaginatorTest.PLUS_POSTS)

    def test_have_index_page_changed_in_the_second_page(self):
        """Проверяет кэшироване главное страницы."""
        resp_p_1 = self.auth_client.get(reverse('posts:index'))
        resp_p_2 = self.auth_client.get(reverse('posts:index'), {'page': 2})
        self.assertNotEqual(resp_p_1.content, resp_p_2.content)
