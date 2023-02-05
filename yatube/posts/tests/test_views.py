from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.paginator import Page
from django.test import Client, TestCase
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Group, Post

User = get_user_model()


class PostViewTest(TestCase):

    @staticmethod
    def extract_post(context):
        post = context.get('post')
        page_obj = context.get('page_obj')
        if post and isinstance(post, Post):
            ext_post = context.get('post')
        elif page_obj and isinstance(page_obj, Page):
            ext_post = context.get('page_obj')[0]
        else:
            raise AssertionError('There is no valid post or '
                                 'page_obj in the context')
        if isinstance(ext_post, Post):
            return ext_post
        else:
            raise AssertionError('The extracting obj is '
                                 'not an instance of Post')

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
        cls.post = Post.objects.create(
            group=cls.group_0,
            text='text of test article',
            author=cls.user_0
        )
        cls.form_fields_list = {
            'group': forms.ChoiceField,
            'text': forms.CharField,
        }

    def setUp(self):
        self.auth_client_0 = Client()
        self.auth_client_0.force_login(PostViewTest.user_0)

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

    def test_correct_page_obj_or_post_in_context(self):
        url_list = [
            reverse('posts:index'),
            reverse('posts:group_list', args=(PostViewTest.group_0.slug,)),
            reverse('posts:profile', args=(PostViewTest.user_0,)),
            reverse('posts:post_detail', args=(PostViewTest.post.pk,)),
        ]
        for url in url_list:
            with self.subTest(url=url):
                context = self.auth_client_0.get(url).context
                self.assertEqual(PostViewTest.extract_post(context).pk,
                                 PostViewTest.post.pk)

    def test_tested_post_not_exist(self):
        url_list = [
            reverse('posts:group_list', args=(PostViewTest.group_1.slug,)),
            reverse('posts:profile', args=(PostViewTest.user_1,)),
        ]
        for url in url_list:
            with self.subTest(url=url):
                with self.assertRaisesMessage(
                        AssertionError,
                        'There is no valid post or page_obj in the context'
                ):
                    context = self.auth_client_0.get(url).context
                    self.assertEqual(PostViewTest.extract_post(context).pk,
                                     PostViewTest.post.pk)

    def test_correct_group_in_context(self):
        """Проверяет коррекстность переданного в контексте объекта group."""
        response = self.auth_client_0.get(
            reverse('posts:group_list', args=(PostViewTest.group_0.slug,))
        )
        group_obj = response.context.get('group')
        self.assertEqual(group_obj, PostViewTest.group_0)

    def test_correct_posts_owner_in_context(self):
        """Проверяет коррекстность переданного в контексте объекта владельца
         поста."""
        response = self.auth_client_0.get(
            reverse('posts:profile', args=(PostViewTest.user_0.username,))
        )
        user_obj = response.context.get('posts_owner')
        self.assertEqual(user_obj, PostViewTest.user_0)

    def test_form_creating_post(self):
        """Проверяет форму создания поста на коррекстность типов полей."""
        response = self.auth_client_0.get(reverse('posts:post_create'))
        for field, form_field in PostViewTest.form_fields_list.items():
            with self.subTest(field=field):
                form_obj = response.context.get('form')
                if isinstance(form_obj, PostForm):
                    field_value = form_obj.fields.get(field)
                    self.assertIsInstance(field_value, form_field)
                else:
                    raise AssertionError('There is no form in context or it '
                                         'is not instance of PostForm')

    def test_form_editing_post(self):
        """Проверяет форму редактирования поста, отфильтрованного по id,
        на коррекстность типов полей."""
        response = self.auth_client_0.get(
            reverse('posts:post_edit', args=(PostViewTest.post.pk,))
        )
        for field, form_field in PostViewTest.form_fields_list.items():
            with self.subTest(field=field):
                form_obj = response.context.get('form')
                if isinstance(form_obj, PostForm):
                    field_value = form_obj.fields.get(field)
                    self.assertIsInstance(field_value, form_field)
                else:
                    raise AssertionError('There is no form in context or it '
                                         'is not instance of PostForm')


class PaginatorTest(TestCase):

    PLUS_POSTS: int = 3

    @staticmethod
    def do_second_page(url: str) -> str:
        """Принимает на вход юрл и возвращает этот же юрл, но с указанием
        на вторую страницу пагинатора."""
        if isinstance(url, str):
            return url + '?page=2'
        raise AssertionError('В функцию do_second_page передан '
                             f'тип {type(url)} вместо str')

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
                resp_2_page = self.auth_client.get(
                    PaginatorTest.do_second_page(url_name))
                len_1page_posts = len(resp_1_page.context.get('page_obj'))
                len_2page_posts = len(resp_2_page.context.get('page_obj'))
                self.assertEqual(len_1page_posts, settings.NUM_OF_POSTS)
                self.assertEqual(len_2page_posts, PaginatorTest.PLUS_POSTS)
