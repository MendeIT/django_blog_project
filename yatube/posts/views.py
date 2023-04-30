from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.shortcuts import get_object_or_404, redirect, render

from posts.forms import CommentForm, PostForm
from posts.models import Group, Follow, Post, User

NUMBER_OF_POST_ON_PAGES = 10


def paginator(request, post_list):
    paginator = Paginator(post_list, NUMBER_OF_POST_ON_PAGES)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20, key_prefix='index_page')
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.select_related('group').all()
    context = {
        'page_obj': paginator(request, post_list),
    }
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    context = {
        'group': group,
        'page_obj': paginator(request, post_list),
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    all_posts_user = author.posts.all()
    post_count = author.posts.count()
    context = {
        'author': author,
        'page_obj': paginator(request, all_posts_user),
        'post_count': post_count,
    }
    if request.user.is_authenticated:
        following = author.following.filter(user=request.user).exists()
        context['following'] = following
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    post_count = post.author.posts.count()
    comments_post = post.comments.all()
    context = {
        'post': post,
        'post_count': post_count,
        'form': CommentForm(request.POST or None),
        'comments': comments_post
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, pk=post_id)
    if post.author == request.user:
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
        if form.is_valid():
            post = form.save()
            return redirect('posts:post_detail', post_id=post.pk)
        context = {
            'post': post,
            'form': form,
            'is_edit': True
        }
        return render(request, template, context)
    return redirect('posts:post_detail', post_id=post.pk)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template_name = 'posts/follow.html'
    post_list = Post.objects.filter(author__following__user=request.user)
    context = {
        'page_obj': paginator(request, post_list)
    }
    return render(request, template_name, context)


@login_required
def profile_follow(request, username):
    following_author = get_object_or_404(User, username=username)
    if request.user != following_author:
        Follow.objects.get_or_create(
            user=request.user,
            author=following_author
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    user_unsubscribe = get_object_or_404(User, username=username)
    if request.user != user_unsubscribe:
        Follow.objects.filter(
            user=request.user,
            author=user_unsubscribe
        ).delete()
    return redirect('posts:profile', username)
