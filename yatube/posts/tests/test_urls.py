from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostUrlTest(TestCase):
    """Тест url приложения posts."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TestUser')
        cls.not_author_user = User.objects.create(username='not_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            group=cls.group,
            text='text of test group',
            author=cls.user
        )

    def setUp(self):
        self.guest_client = Client()
        self.auth_client = Client()
        self.not_author_client = Client()
        self.auth_client.force_login(PostUrlTest.user)
        self.not_author_client.force_login(PostUrlTest.not_author_user)
        self.url_dict_unauth = {
            '/': 'posts/index.html',
            f'/group/{PostUrlTest.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostUrlTest.user.username}/': 'posts/profile.html',
            f'/posts/{PostUrlTest.post.id}/': 'posts/post_detail.html',
        }
        self.url_dict_auth = {
            '/create/': 'posts/create_post.html',
            f'/posts/{PostUrlTest.post.id}/edit/': 'posts/create_post.html',
        }
        self.redirect_dict_unauth = {
            '/create/': '/auth/login/?next=/create/',
            (f'/posts/{PostUrlTest.post.id}/'
             f'edit/'): f'/auth/login/?next=/posts/{PostUrlTest.post.id}/edit/'
        }
        self.unexisting_url = {'/unexisting_page/': 'core/404.html'}

    def test_url_exists_at_desired_location_for_unauth_users(self):
        """Проверяет, существуют ли страницы для неавторизованных юзеров."""
        for url in self.url_dict_unauth:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_at_desired_location_for_auth_users(self):
        """Проверяет, существуют ли страницы для авторизованных юзеров."""
        self.url_dict_auth.update(self.url_dict_unauth)
        for url in self.url_dict_auth:
            with self.subTest(url=url):
                response = self.auth_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page_url_for_auth_users(self):
        """Проверяет, что возникает ошибка при переходе на
        несуществующий url."""
        for url in self.unexisting_url.keys():
            response = self.auth_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_redirect_if_post_by_not_author_but_auth_user(self):
        """Проверяет будет ли редирект со страницы правки поста
        для зарегистрированного юзера, не являющегося его автором."""
        response = self.not_author_client.get('/posts/1/edit/')
        self.assertRedirects(response, '/posts/1/')

    def test_redirect_for_unauth_user(self):
        """Проверяет будет ли редирект для неавторизованных юзеров."""
        for url, aim in self.redirect_dict_unauth.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, aim)

    def test_correct_template_for_unauth(self):
        """Проверяет корректность шаблонов для неавторизованных юзеров."""
        for url, template in self.url_dict_unauth.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_correct_template_for_auth(self):
        """Проверяет корректность шаблонов для авторизованных юзеров."""
        self.url_dict_auth.update(self.url_dict_unauth)
        for url, template in self.url_dict_auth.items():
            with self.subTest(url=url):
                response = self.auth_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_correct_template_for_404(self):
        """Проверяет корректность шаблонов ошибки 404."""
        for url, template in self.unexisting_url.items():
            with self.subTest(url=url):
                response = self.auth_client.get(url)
                self.assertTemplateUsed(response, template)
