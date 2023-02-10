import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.models import Group, Post, Comment

TEMP_MEDIA_ROOT = tempfile.mktemp(dir=settings.BASE_DIR)
User = get_user_model()


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.auth_client = Client()
        self.auth_client.force_login(TestPostForm.user)
        self.post = Post.objects.create(
            group=TestPostForm.group_0,
            text='test text',
            author=TestPostForm.user
        )
        self.comm_data = {'text': 'test comment'}

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

    def test_create_post_with_img(self):
        Post.objects.all().delete()
        img_data = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.jpg',
            content=img_data,
            content_type='image/jpeg'
        )
        form_data = {
            'text': 'Article with uploaded image',
            'image': uploaded,
        }
        response = self.auth_client.post(
            path=reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', args=(TestPostForm.user.username,)))
        self.assertEqual(1, Post.objects.count())
        upload_dir = self.post._meta.get_field('image').upload_to
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                image=f'{upload_dir}{uploaded.name}'
            ).exists()
        )

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

    def test_create_comment(self):
        Comment.objects.all().delete()
        response = self.auth_client.post(
            path=reverse('posts:add_comment', args=(self.post.pk,)),
            data=self.comm_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=(self.post.pk,)))
        self.assertEqual(1, Comment.objects.count())
        self.assertTrue(
            Comment.objects.filter(
                text=self.comm_data['text'],
                post=self.post.id,
                author=TestPostForm.user.id
            ).exists()
        )

    def test_create_comment_by_unauth_user(self):
        Comment.objects.all().delete()
        response = self.guest_client.post(
            path=reverse('posts:add_comment', args=(self.post.pk,)),
            data=self.comm_data,
            follow=True
        )
        self.assertRedirects(
            response,
            (reverse('users:login') +
             f'?next=/posts/{self.post.pk}/comment/')
        )
        self.assertEqual(0, Comment.objects.count())
