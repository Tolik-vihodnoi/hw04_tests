from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm
from .models import Group, Post, User
from .utils import do_page_obj


def index(request):
    posts = Post.objects.select_related('author',
                                        'group')
    page_obj = do_page_obj(request, posts, settings.NUM_OF_POSTS)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.select_related('author', 'group')
    page_obj = do_page_obj(request, posts, settings.NUM_OF_POSTS)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    posts_owner = get_object_or_404(User, username=username)
    posts = posts_owner.posts.select_related('author', 'group')
    page_obj = do_page_obj(request, posts, settings.NUM_OF_POSTS)
    context = {
        'page_obj': page_obj,
        'posts_owner': posts_owner
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        pk=post_id
    )
    context = {
        'post': post
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form})
    save_form = form.save(commit=False)
    save_form.author = request.user
    save_form.save()
    return redirect('posts:profile', request.user.username)


@login_required
def post_edit(request, post_id):
    post_obj = get_object_or_404(Post, id=post_id)
    if request.user != post_obj.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(request.POST or None, instance=post_obj)
    if not form.is_valid():
        return render(request, 'posts/create_post.html', {'form': form,
                                                          'post_id': post_id})
    form.save()
    return redirect('posts:post_detail', post_id)
