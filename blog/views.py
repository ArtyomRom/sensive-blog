from django.shortcuts import render
from blog.models import Comment, Post, Tag
from django.db.models import Subquery, OuterRef, Count, IntegerField


def get_related_posts_count(tag):
    return tag.posts.count()


def serialize_post(post):
    related_tags = post.tags.annotate(posts_count=Count('posts'))
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount': len(Comment.objects.filter(post=post)),
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
        'first_tag_title': post.tags.all()[0].title,
    }


def serialize_tag(tag):
    return {
        'title': tag.title,
       # 'posts_with_tag': len(Post.objects.filter(tags=tag)),
        'posts_with_tag': tag.posts_count
    }

def get_likes_count(post):
    return post.likes.count()


def get_most_popular_posts(limit=5):
    # Подзапрос для лайков
    likes_subquery = Post.objects.filter(pk=OuterRef('pk')) \
                         .annotate(cnt=Count('likes')) \
                         .values('cnt')[:1]

    # Подзапрос для комментариев
    comments_subquery = Post.objects.filter(pk=OuterRef('pk')) \
                            .annotate(cnt=Count('comment')) \
                            .values('cnt')[:1]

    return Post.objects.select_related('author') \
               .prefetch_related('tags') \
               .annotate(
        likes_count=Subquery(likes_subquery, output_field=IntegerField()),
        comments_count=Subquery(comments_subquery, output_field=IntegerField())
    ) \
               .order_by('-likes_count')[:limit]

# def get_most_popular_tags(limit=5):
#     return Tag.objects.prefetch_related('posts') \
#         .annotate(posts_count=Count('posts')) \
#         .order_by('-posts_count')[:limit]

def serialize_post_optimized(post):
    related_tags = list(post.tags.annotate(posts_count=Count('posts')))
    return {
        'title': post.title,
        'teaser_text': post.text[:200],
        'author': post.author.username,
        'comments_amount':  post.comments_count,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
        'first_tag_title': related_tags[0].title if related_tags else '',
    }

def index(request):

    most_popular_posts = get_most_popular_posts()

    fresh_posts = Post.objects \
                      .select_related('author') \
                      .prefetch_related('tags') \
                      .annotate(comments_count=Count('comment', distinct=True)) \
                      .order_by('-published_at')[:5]

    most_fresh_posts = list(fresh_posts)[-5:]

    most_popular_tags = Tag.objects.popular()


    context = {
        'most_popular_posts': [
            serialize_post_optimized(post) for post in most_popular_posts
        ],
        'page_posts': [serialize_post_optimized(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)



def post_detail(request, slug):
    post = Post.objects.prefetch_related('tags', 'author').get(slug=slug)
    #comments = Comment.objects.filter(post=post)
    comments = Comment.objects.filter(post=post).select_related('author')
    serialized_comments = []
    for comment in comments:
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })

    likes = post.likes.count()

    related_tags = post.tags.annotate(posts_count=Count('posts'))

    serialized_post = {
        'title': post.title,
        'text': post.text,
        'author': post.author.username,
        'comments': serialized_comments,
        'likes_amount': likes,
        'image_url': post.image.url if post.image else None,
        'published_at': post.published_at,
        'slug': post.slug,
        'tags': [serialize_tag(tag) for tag in related_tags],
    }

    most_popular_tags = Tag.objects.popular()
    most_popular_posts = get_most_popular_posts()
    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = Tag.objects.annotate(posts_count=Count('posts')).get(title=tag_title)

    most_popular_tags = Tag.objects.popular()
    most_popular_posts = get_most_popular_posts()

    related_posts = tag.posts.all()[:20]

    context = {
        'tag': tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'posts': [serialize_post(post) for post in related_posts],
        'most_popular_posts': [
            serialize_post(post) for post in most_popular_posts
        ],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
