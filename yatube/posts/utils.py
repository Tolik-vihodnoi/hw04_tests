from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404

from .models import User


def do_page_obj(request, q_set, num_of_items):
    page_num = request.GET.get('page')
    paginator = Paginator(q_set, num_of_items)
    return paginator.get_page(page_num)


def extract_user_author(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    return {'user': user, 'author': author}
