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
        cls.form_data = {
            'text': 'Just a correct text',
            'group': TestPostForm.group_1.pk
        }

    def setUp(self):
        self.auth_client = Client()
        self.auth_client.force_login(TestPostForm.user)
        self.post = Post.objects.create(
            group=TestPostForm.group_0,
            text='test text',
            author=TestPostForm.user
        )

    def tearDown(self) -> None:
        Post.objects.all().delete()

    def test_create_post(self):
        Post.objects.all().delete()
        response = self.auth_client.post(
            path=reverse('posts:post_create'),
            data=TestPostForm.form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', args=(TestPostForm.user.username,)))
        self.assertEqual(Post.objects.count(), 1)
        post_obj = Post.objects.first()
        self.assertEqual(post_obj.text,
                         TestPostForm.form_data['text'])
        self.assertEqual(post_obj.group.pk,
                         TestPostForm.form_data['group'])

    def test_edit_post(self):
        response = self.auth_client.post(
            path=reverse('posts:post_edit',
                         kwargs={'post_id': self.post.id}),
            data=TestPostForm.form_data,
            follow=True
        )
        post_obj = Post.objects.get(id=self.post.id)
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            args=(self.post.id,)
        ))
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(post_obj.text, TestPostForm.form_data['text'])
        self.assertEqual(post_obj.group.pk, TestPostForm.form_data['group'])
