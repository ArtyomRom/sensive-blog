from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Subquery, OuterRef, Count, IntegerField
from django.db.models import Prefetch

class PostQuerySet(models.QuerySet):

    def year(self, year):
        posts_at_year = self.filter(published_at__year=year).order_by('published_at')
        return posts_at_year

    def popular(self):
        likes_subquery = self.model.objects.filter(pk=OuterRef('pk')) \
                             .annotate(cnt=Count('likes')) \
                             .values('cnt')[:1]

        comments_subquery = self.model.objects.filter(pk=OuterRef('pk')) \
                                .annotate(cnt=Count('comments')) \
                                .values('cnt')[:1]

        return self.select_related('author') \
            .prefetch_related('tags') \
            .annotate(
            likes_count=Subquery(likes_subquery, output_field=IntegerField()),
            comments_count=Subquery(comments_subquery, output_field=IntegerField())
        ) \
            .order_by('-likes_count')

    def fresh_posts(self):
        tags_with_posts_count = Tag.objects.annotate(posts_count=Count('posts'))

        return self.select_related('author') \
                          .prefetch_related(Prefetch('tags', queryset=tags_with_posts_count)) \
                          .annotate(comments_count=Count('comments', distinct=True)) \
                          .order_by('-published_at')[:5]

class TagQuerySet(models.QuerySet):
    def popular(self):
        return self.annotate(posts_count=Count('posts')) \
                   .order_by('-posts_count')


class TagManager(models.Manager):
    def get_queryset(self):
        return TagQuerySet(self.model, using=self._db)

    def popular(self):
        return self.get_queryset().popular()


class Post(models.Model):
    title = models.CharField('Заголовок', max_length=200)
    text = models.TextField('Текст')
    slug = models.SlugField('Название в виде url', max_length=200)
    image = models.ImageField('Картинка')
    published_at = models.DateTimeField('Дата и время публикации')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор',
        limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        verbose_name='Кто лайкнул',
        blank=True)
    tags = models.ManyToManyField(
        'Tag',
        related_name='posts',
        verbose_name='Теги')


    objects = PostQuerySet.as_manager()


    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})


class Tag(models.Model):
    title = models.CharField('Тег', max_length=20, unique=True)
    objects = TagManager()
    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    class Meta:
        ordering = ['title']
        verbose_name = 'тег'
        verbose_name_plural = 'теги'


class Comment(models.Model):
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост, к которому написан')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор')

    text = models.TextField('Текст комментария')
    published_at = models.DateTimeField('Дата и время публикации')



    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'

    def __str__(self):
        return f'{self.author.username} under {self.post.title}'
