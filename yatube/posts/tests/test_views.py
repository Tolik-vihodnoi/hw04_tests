from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.paginator import Page

from posts.models import Group, Post

User = get_user_model()


class PostViewTest(TestCase):

    def do_url_last_page(self, url: str) -> str:
        """Принимает на вход валидный юрл, принимает из контекста page_obj и
        возвращает юрл с указанием на последнюю страницу пагинатора."""
        response = self.auth_client_0.get(url)
        page_obj = response.context.get('page_obj')
        if isinstance(page_obj, Page):
            last_page_value = page_obj.paginator.num_pages
            return url + f'?page={str(last_page_value)}'
        raise Exception('Контекст страницы не содержит объекта page_obj')

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
        for i in range(28):
            Post.objects.create(
                group=cls.group_0 if i <= 14 else cls.group_1,
                text=f'text of article number {i}',
                author=cls.user_0 if i <= 14 else cls.user_1,
            )

    def setUp(self):
        self.url_name_dict = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostViewTest.group_0.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostViewTest.user_0}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': 12}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': 12}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        self.auth_client_0 = Client()
        self.auth_client_0.force_login(PostViewTest.user_0)
        self.post_count = Post.objects.count()
        self.count_gr0_post = Post.objects.filter(
            group=PostViewTest.group_0).count()
        self.count_u1_post = Post.objects.filter(
            author=PostViewTest.user_1).count()

    def test_pages_use_correct_templates(self):
        """Проверяет, что namespace:name вызывает корректные шаблоны"""
        for url_name, templ in self.url_name_dict.items():
            with self.subTest(url_name=url_name):
                response = self.auth_client_0.get(url_name)
                self.assertTemplateUsed(response, templ)

    def test_pages_use_correct_context_filtered_page_obj(self):
        """Проверяет корректность использованных в контексте page_obj,
        отсортированных по группе или автору в зависимости от адреса"""
        url_list = [
            (reverse('posts:index') + '?page=3'),
            reverse('posts:group_list',
                    kwargs={'slug': PostViewTest.group_0.slug}),
            reverse('posts:profile',
                    kwargs={'username': PostViewTest.user_0.username})
        ]
        for url_name in url_list:
            with self.subTest(url_name=url_name):
                response = self.auth_client_0.get(url_name)
                first_obj = response.context.get('page_obj')[0]
                post_group = first_obj.group.title
                post_text = first_obj.text
                post_author = first_obj.author.username
                self.assertEqual(post_group, PostViewTest.group_0.title)
                self.assertEqual(
                    post_text,
                    ('text of article number 7' if url_name == url_list[0]
                     else 'text of article number 14')
                )
                self.assertEqual(post_author, PostViewTest.user_0.username)

    def test_pages_use_correct_context_group(self):
        """Проверяет коррекстность переданного в контексте объекта group."""
        response = self.auth_client_0.get(
            reverse('posts:group_list',
                    kwargs={'slug': PostViewTest.group_0.slug})
        )
        group_obj = response.context.get('group')
        self.assertEqual(group_obj.title, PostViewTest.group_0.title)
        self.assertEqual(group_obj.slug, PostViewTest.group_0.slug)
        self.assertEqual(group_obj.description,
                         PostViewTest.group_0.description)

    def test_pages_use_correct_context_posts_owner(self):
        """Проверяет коррекстность переданного в контексте объекта владельца
         поста."""
        response = self.auth_client_0.get(
            reverse('posts:profile',
                    kwargs={'username': PostViewTest.user_0.username})
        )
        user_obj = response.context.get('posts_owner')
        self.assertEqual(user_obj.username, PostViewTest.user_0.username)

    def test_pages_use_correct_context_post(self):
        """Проверяет коррекстность переданного в контексте поста,
        отфильтрованного по id."""
        response = self.auth_client_0.get(
            reverse('posts:post_detail', kwargs={'post_id': 20})
        )
        post_obj = response.context.get('post')
        self.assertEqual(post_obj.group.title, PostViewTest.group_1.title)
        self.assertEqual(post_obj.text, 'text of article number 19')
        self.assertEqual(post_obj.author.username,
                         PostViewTest.user_1.username)

    def test_form_creating_post(self):
        """Проверяет форму создания поста на коррекстность типов полей."""
        form_fields_list = {
            'group': forms.ChoiceField,
            'text': forms.CharField,
        }
        response = self.auth_client_0.get(reverse('posts:post_create'))
        for field, form_field in form_fields_list.items():
            with self.subTest(field=field):
                resp_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(resp_field, form_field)

    def test_form_editing_post(self):
        """Проверяет форму редактирования поста на коррекстность
        типов полей."""
        form_fields_list = {
            'group': forms.ChoiceField,
            'text': forms.CharField,
        }
        response = self.auth_client_0.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': 1})
        )
        for field, form_field in form_fields_list.items():
            with self.subTest(field=field):
                resp_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(resp_field, form_field)

    def test_paginator(self):
        """Проверяет пагинатор на соответствие назначенному кол-ву объектов
        на первой странице и последней."""
        posts_mod = Post.objects.count() % settings.NUM_OF_POSTS
        gr0_posts_mod = Post.objects.filter(
            group=PostViewTest.group_0).count() % settings.NUM_OF_POSTS
        u1_posts_mod = Post.objects.filter(
            author=PostViewTest.user_1).count() % settings.NUM_OF_POSTS
        count_posts_dict = {
            reverse('posts:index'): settings.NUM_OF_POSTS,
            PostViewTest.do_url_last_page(self, reverse('posts:index')): posts_mod,
            reverse('posts:group_list',
                    args=(PostViewTest.group_0.slug,)): settings.NUM_OF_POSTS,
            PostViewTest.do_url_last_page(self, reverse(
                'posts:group_list',
                args=(PostViewTest.group_0.slug,))): gr0_posts_mod,
            reverse('posts:profile',
                    kwargs={'username': PostViewTest.user_1.username
                            }): settings.NUM_OF_POSTS,
            PostViewTest.do_url_last_page(self, reverse(
                'posts:profile',
                args=(PostViewTest.user_1.username,))): u1_posts_mod,
        }
        for url_name, num_of_posts in count_posts_dict.items():
            with self.subTest(url_name=url_name):
                response = self.auth_client_0.get(url_name)
                len_posts = len(response.context.get('page_obj'))
                self.assertEqual(len_posts, num_of_posts)
