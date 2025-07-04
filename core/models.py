# your_app/models.py

from django.db import models
from django.contrib.auth.models import User
from taggit.managers import TaggableManager
from django_resized import ResizedImageField
from django_ckeditor_5.fields import CKEditor5Field
from django.urls import reverse

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    thumbnail = ResizedImageField(
        size=[300, 450],
        quality=85,
        upload_to='thumbnails/',
        blank=True,
        null=True,
        help_text="Upload featured image (recommended size: 300x450px)"
    )
    content = CKEditor5Field('Text', config_name='default')

    excerpt = models.TextField(
        blank=True,
        help_text="A brief summary of the post, used for previews (e.g., on index pages, social media, Telegram)."
    )

    # ADD THIS LINE FOR THE VIEWS COUNT
    views = models.IntegerField(default=0) # Added this line for tracking views
    # END ADDITION

    enable_downloads = models.BooleanField(
        default=True,
        help_text="Show download section for this post"
    )
    download_section_title = models.CharField(
        max_length=100,
        default="Download Links",
        blank=True
    )
    download_button_text = models.CharField(
        max_length=50,
        default="Download Now",
        blank=True
    )
    download_url = models.URLField(blank=True)
    subtitle_url = models.URLField(blank=True)
    subtitle_button_text = models.CharField(
        max_length=50,
        default="Download Subtitle",
        blank=True
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    tags = TaggableManager()  # Tags using django-taggit
    published_date = models.DateTimeField(auto_now_add=True)
    is_published = models.BooleanField(default=True)


    def get_absolute_url(self):
        # This assumes your post detail URL pattern is named 'post_detail'
        # and expects 'category' and 'slug' kwargs.
        # Ensure your urls.py matches this.
        return reverse('post_detail', kwargs={
            'category': self.category.slug,
            'slug': self.slug
        })

    def __str__(self):
        return self.title
    
class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=100)
    email = models.EmailField()
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Comment"
        verbose_name_plural = "Comments"

    def __str__(self):
        return f"Comment by {self.name} on {self.post.title}"
    
# from django.db import models # Already imported above

class HomepageSection(models.Model):
    """Admin-configurable sections for homepage"""
    title = models.CharField(max_length=100)
    categories = models.ManyToManyField('Category', blank=True)
    enabled = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['display_order']
    
    def __str__(self):
        return self.title

class DownloadQuality(models.Model):
    QUALITY_CHOICES = [
        ('360p', 'DOWNLOAD [360p]'),
        ('480p', 'DOWNLOAD [480p]'), 
        ('720p', 'DOWNLOAD [720p (HD)]'),
        ('1080p', 'DOWNLOAD [1080p (FHD)]'),
        ('4K', 'DOWNLOAD [4K (UHD)]'),
    ]
    
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='qualities')
    quality = models.CharField(max_length=10, choices=QUALITY_CHOICES)
    download_url = models.URLField()
    download_count = models.PositiveIntegerField(default=0)
    is_premium = models.BooleanField(default=False)

class Subtitle(models.Model):
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='subtitles')
    language = models.CharField(max_length=50)
    download_url = models.URLField()
    is_auto_generated = models.BooleanField(default=False)
    download_count = models.PositiveIntegerField(default=0)