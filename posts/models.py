from django.db import models
from django.conf import settings
from django.urls import reverse
from django.utils.text import slugify
import uuid


class Category(models.Model):
    """Blog post categories."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(max_length=300, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def post_count(self):
        return self.posts.count()


class Tag(models.Model):
    """Tags for blog posts."""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=60, unique=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Strip any leading # from the name
        self.name = self.name.lstrip('#').strip()
        if not self.slug:
            # Map special programming chars to words so they aren't stripped
            safe_name = self.name.lower()
            safe_name = safe_name.replace('++', 'plusplus')\
                                 .replace('+', 'plus')\
                                 .replace('#', 'sharp')\
                                 .replace('.', 'dot')
            
            base_slug = slugify(safe_name) or 'tag'
            
            slug = base_slug
            counter = 1
            while Tag.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
            
        super().save(*args, **kwargs)


class Post(models.Model):
    """Blog post model."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        PUBLISHED = 'published', 'Published'

    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=250, unique=True, blank=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
    )
    content = models.TextField(help_text='Write your blog post content here.')
    excerpt = models.TextField(
        max_length=500,
        blank=True,
        default='',
        help_text='A short summary shown on listing pages.',
    )
    cover_image = models.ImageField(
        upload_to='posts/covers/%Y/%m/',
        blank=True,
        null=True,
        help_text='Cover image for the post.',
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    featured = models.BooleanField(default=False, help_text='Show on featured section.')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            self.slug = f"{base_slug}-{uuid.uuid4().hex[:8]}"
        if not self.excerpt and self.content:
            self.excerpt = self.content[:200].strip()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('posts:detail', kwargs={'slug': self.slug})

    @property
    def like_count(self):
        return self.likes.count()

    @property
    def comment_count(self):
        return self.comments.count()

    @property
    def reading_time(self):
        """Estimated reading time in minutes."""
        word_count = len(self.content.split())
        minutes = max(1, round(word_count / 200))
        return minutes
