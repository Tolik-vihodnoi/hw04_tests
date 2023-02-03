from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post


User = get_user_model()


class TestPostForm(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='TolikVihodnoi')
        cls.group_0 = Group.objects.create(
            title='Test group_0',
            slug='test_group_0',
        )
        cls.group_1 = Group.objects.create(
            title='Test group_1',
            slug='test_group_1'
        )
        cls.post = Post.objects.create(
            group=cls.group_0,
            text='test text',
            author=cls.user
        )
        cls.form_data = {
            'text': 'Just a correct text',
            'group': TestPostForm.group_1.pk
        }
        cls.redirects = {
            reverse
        }

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(TestPostForm.user)

    def test_create_post(self):
        post_count = Post.objects.count()

        response = self.auth_client.post(
            path=reverse('posts:post_create'),
            data=TestPostForm.form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile',
            args=(TestPostForm.user.username,)
        ))
        self.assertEqual(post_count + 1, Post.objects.count())

    def test_edit_post(self):
        post_count = Post.objects.count()
        response = self.auth_client.post(
            path=reverse('posts:post_edit',
                         kwargs={'post_id': TestPostForm.post.id}),
            data=TestPostForm.form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=(TestPostForm.post.id,)
        ))
        self.assertEqual(post_count, Post.objects.count())
        self.assertEqual(Post.objects.get(id=TestPostForm.post.id).text,
                         TestPostForm.form_data.get('text'))
        self.assertEqual(Post.objects.get(id=TestPostForm.post.id).group.slug,
                         TestPostForm.group_1.slug)
