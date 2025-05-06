from django.shortcuts import render
from blog.models import Comment, Post, Tag
from django.db.models import Count
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404


def get_data_for_context():
    most_popular_posts = Post.objects.popular()[:5]
    fresh_posts = Post.objects.fresh_posts()
    most_popular_tags = Tag.objects.popular()

    return {
        'most_popular_posts': most_popular_posts,
        'fresh_posts': fresh_posts,
        'most_popular_tags': most_popular_tags,
    }


def serialize_post(post):
    related_tags = post.tags.all()
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': post.comments_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
        'first_tag_title': post.tags.first().title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
        'posts_with_tag': getattr(tag, 'posts_count', 0)
    }



def index(request):
    data = get_data_for_context()
    most_popular_posts = data['most_popular_posts']
    most_fresh_posts = data['fresh_posts']
    most_popular_tags = data['most_popular_tags']


    context = {
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
        'page_posts': [serialize_post(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)



def post_detail(request, slug):
    post = get_object_or_404(
        Post.objects.select_related('author')
        .prefetch_related('tags')
        .annotate(likes_count=Count('likes'))
        .annotate(comments_count=Count('comments')),
        slug=slug)
    comments = post.comments.select_related('author')
    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })



    related_tags = post.tags.annotate(posts_count=Count('posts'))

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': post.likes_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
    }
    data = get_data_for_context()
    most_popular_tags = data['most_popular_tags']
    most_popular_posts = data['most_popular_posts']
    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = get_object_or_404(Tag.objects.annotate(posts_count=Count('posts')), title=tag_title)
    data = get_data_for_context()
    most_popular_tags = data['most_popular_tags']
    most_popular_posts = data['most_popular_posts']

    tags_with_counts = Tag.objects.annotate(posts_count=Count('posts'))

    related_posts = tag.posts \
        .select_related('author') \
        .prefetch_related(Prefetch('tags', queryset=tags_with_counts)) \
        .annotate(comments_count=Count('comments', distinct=True))[:20]

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [serialize_post(post) for post in most_popular_posts],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
