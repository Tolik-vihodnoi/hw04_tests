from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    """Тест моделей приложения posts."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='user_for_tests')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        for obj in (PostModelTest.post, PostModelTest.group):
            with self.subTest(obj=obj):
                self.assertEqual(
                    obj.text[:settings.DISP_LETTERS] if isinstance(obj, Post)
                    else obj.title, str(obj))

    def test_models_have_correct_object_help_text(self):
        """Проверяем, что у моделей Post корректно работает help_text."""
        field_dict = {'group': 'Группа, к которой будет относиться пост',
                      'text': 'Текст нового поста'}
        for f, text in field_dict.items():
            with self.subTest(f=f):
                self.assertEqual(
                    PostModelTest.post._meta.get_field(f).help_text,
                    text
                )
