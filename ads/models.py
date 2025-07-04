# ads/models.py
from django.db import models
from django_resized import ResizedImageField # Assuming you use django-resized for images
from django.urls import reverse

class AdPlacement(models.Model):
    """
    Defines a specific location on the website where ads can be displayed.
    Examples: 'Sidebar Top', 'Below Post Title', 'Footer Banner'
    """
    name = models.CharField(max_length=100, unique=True, help_text="A unique name for this ad placement (e.g., 'Sidebar Top', 'Below Post Content')")
    slug = models.SlugField(max_length=100, unique=True, help_text="A unique slug for URL or template identification")
    description = models.TextField(blank=True, help_text="Brief description of where this placement appears.")
    width = models.IntegerField(blank=True, null=True, help_text="Recommended width for ads in this placement (in pixels)")
    height = models.IntegerField(blank=True, null=True, help_text="Recommended height for ads in this placement (in pixels)")
    is_active = models.BooleanField(default=True, help_text="Whether this ad placement is currently active on the site.")

    class Meta:
        verbose_name = "Ad Placement"
        verbose_name_plural = "Ad Placements"
        ordering = ['name']

    def __str__(self):
        return self.name

class Ad(models.Model):
    """
    Represents an individual ad creative.
    """
    placement = models.ForeignKey(
        AdPlacement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ads',
        help_text="The location where this ad is intended to be displayed."
    )
    name = models.CharField(max_length=200, help_text="Internal name for the ad creative.")
    image = ResizedImageField(
        size=[1200, 800], # Max size, adjust as needed for your common ad sizes
        quality=85,
        upload_to='ads/',
        blank=True,
        null=True,
        help_text="Upload the ad image (e.g., banner, square ad)."
    )
    code = models.TextField(
        blank=True,
        help_text="HTML/JavaScript code for the ad (e.g., Google AdSense, direct HTML banner). "
                  "If code is provided, image and target_url might be ignored."
    )
    target_url = models.URLField(
        blank=True,
        help_text="The URL the user will be redirected to when clicking the ad image."
    )
    alt_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Alt text for the ad image, important for accessibility and SEO."
    )
    start_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date and time when the ad should start appearing."
    )
    end_date = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date and time when the ad should stop appearing."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this ad is currently active and eligible for display."
    )
    views = models.PositiveIntegerField(default=0, help_text="Number of times this ad has been displayed.")
    clicks = models.PositiveIntegerField(default=0, help_text="Number of times this ad has been clicked.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Ad Creative"
        verbose_name_plural = "Ad Creatives"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def get_ad_url(self):
        """Returns the URL to track clicks for this ad."""
        # You'll need to define a URL pattern for ad clicks in ads/urls.py
        # For now, it can just return the target_url or a placeholder.
        if self.target_url:
            return reverse('ads:ad_click', kwargs={'pk': self.pk})
        return "#" # Fallback if no target URL

    def is_currently_active(self):
        """Checks if the ad is active based on its dates and is_active flag."""
        from django.utils import timezone
        now = timezone.now()
        return (
            self.is_active and
            (self.start_date is None or self.start_date <= now) and
            (self.end_date is None or self.end_date >= now)
        )

