# ads/context_processors.py
from django.db import models # <-- ADDED THIS IMPORT
from .models import AdPlacement, Ad
from django.utils import timezone
import random # Import random for a potentially safer way to get one random item

def active_ads(request):
    """
    Context processor to make active ads available in all templates.
    It fetches a random active ad for each active ad placement.
    """
    context = {}
    
    # Ensure AdPlacement and Ad models exist before querying
    try:
        # Filter for active placements
        active_placements = AdPlacement.objects.filter(is_active=True)
    except Exception as e:
        # Log the error, but don't break the site
        print(f"Error fetching AdPlacements: {e}")
        return {} # Return empty context if models or DB are problematic

    for placement in active_placements:
        try:
            # Filter by is_active, and the ad's start/end dates
            # Corrected: The date filtering should apply directly to Ad model's dates,
            # not conditionally based on placement's non-existent date fields.
            now = timezone.now()
            eligible_ads = Ad.objects.filter(
                placement=placement,
                is_active=True
            ).filter(
                # Filter for ads where start_date is null OR start_date is in the past/now
                models.Q(start_date__isnull=True) | models.Q(start_date__lte=now)
            ).filter(
                # Filter for ads where end_date is null OR end_date is in the future/now
                models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
            )
            
            # If there are eligible ads, pick one randomly and increment views
            if eligible_ads.exists():
                # Get all eligible ads and pick one randomly in Python for robustness
                # This avoids potential DB issues with order_by('?') on some backends
                ad = random.choice(list(eligible_ads))
                ad.views += 1
                ad.save(update_fields=['views']) # Only update the views field
                context[f'ad_placement_{placement.slug}'] = ad
            else:
                context[f'ad_placement_{placement.slug}'] = None # No active ad for this placement
        except Exception as e:
            # Log any error for a specific ad/placement, but continue processing others
            print(f"Error processing ad for placement '{placement.slug}': {e}")
            context[f'ad_placement_{placement.slug}'] = None # Ensure it's None on error

    return context
