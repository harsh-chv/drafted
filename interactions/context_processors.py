from django.utils import timezone
from datetime import timedelta
from .models import Notification, Note

def unread_notification_count(request):
    """Inject unread notification count into every template context."""
    if request.user.is_authenticated:
        count = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()
        return {'unread_notification_count': count}
    return {'unread_notification_count': 0}

def active_notes_processor(request):
    """Inject active notes (created within 24h) from followed users."""
    if request.user.is_authenticated:
        # Notes from current user and users they follow
        following_users = request.user.following.values_list('following_id', flat=True)
        recent_time = timezone.now() - timedelta(hours=24)
        
        # Collect distinct notes for user's followings and the user themselves
        from django.db.models import Prefetch
        active_notes = Note.objects.filter(
            user_id__in=list(following_users) + [request.user.id],
            created_at__gte=recent_time
        ).select_related('user').order_by('-created_at')
        
        # We only want the most recent note per user.
        user_notes = {}
        for note in active_notes:
            if note.user_id not in user_notes:
                user_notes[note.user_id] = note
                
        return {'active_notes': list(user_notes.values())}
    return {'active_notes': []}
