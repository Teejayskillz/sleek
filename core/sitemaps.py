# core/sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from core.models import Post # Import Post model from your core app

class PostSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.9

    def items(self):
        # IMPORTANT CHANGE: Filter for posts that are published AND have a category assigned
        # This prevents errors if a Post's category is null.
        return Post.objects.filter(is_published=True, category__isnull=False).order_by('-published_date')

    def lastmod(self, obj):
        # Return the last modification date for each post.
        # Use updated_date if it exists and is set, otherwise fall back to published_date.
        return obj.updated_date if hasattr(obj, 'updated_date') and obj.updated_date else obj.published_date

    def location(self, obj):
        # This calls the get_absolute_url() method on your Post model.
        # Since we're filtering for category__isnull=False in items(),
        # obj.category will always be a valid Category object here.
        return obj.get_absolute_url()

# You can add more Sitemap classes for other models/pages if needed.
class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "monthly"

    def items(self):
        # List the names of your static views (e.g., home, about, contact)
        # Ensure these names exist in your core/urls.py or project urls.py
        return ['home', 'search'] # Updated based on your core/urls.py, add others as needed

    def location(self, item):
        return reverse(item)
