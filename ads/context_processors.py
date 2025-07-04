# ads/context_processors.py
from .models import AdPlacement, Ad
from django.utils import timezone

def active_ads(request):
    """
    Context processor to make active ads available in all templates.
    It fetches a random active ad for each active ad placement.
    """
    context = {}
    active_placements = AdPlacement.objects.filter(is_active=True)

    for placement in active_placements:
        # Get a random active ad for this placement
        # Filter by is_active, start_date, end_date, and order randomly
        # We also increment the view count here.
        eligible_ads = Ad.objects.filter(
            placement=placement,
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        ).order_by('?') # Order randomly

        if eligible_ads.exists():
            ad = eligible_ads.first() # Get the first random ad
            ad.views += 1
            ad.save(update_fields=['views']) # Only update the views field
            context[f'ad_placement_{placement.slug}'] = ad
        else:
            context[f'ad_placement_{placement.slug}'] = None

    return context
