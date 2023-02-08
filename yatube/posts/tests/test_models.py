from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostTest(TestCase):
    """Тест моделей приложения posts."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user_for_tests')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание для проверки',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост для проверки',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        models = {
            PostTest.post: PostTest.post.text[:settings.DISP_LETTERS],
            PostTest.group: PostTest.group.title
        }
        for obj, field in models.items():
            with self.subTest(obj=obj):
                self.assertEqual(field, str(obj))

    def test_models_have_correct_object_help_text(self):
        """Проверяем, что у моделей Post корректно работает help_text."""
        field_dict = {'group': 'Группа, к которой будет относиться пост',
                      'text': 'Текст нового поста'}
        for field, text in field_dict.items():
            with self.subTest(field=field):
                self.assertEqual(
                    PostTest.post._meta.get_field(field).help_text,
                    text
                )
