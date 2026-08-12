from django.shortcuts import redirect, get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from posts.models import Post
from users.models import User
from .models import Comment, Like, Follow, Notification
from .forms import CommentForm


def _create_notification(recipient, actor, action, post=None):
    """Helper to create a notification (never notify yourself)."""
    if recipient != actor:
        Notification.objects.create(
            recipient=recipient,
            actor=actor,
            action=action,
            post=post,
        )


@login_required
def like_toggle_view(request, post_id):
    """Toggle like/unlike on a post."""
    post = get_object_or_404(Post, pk=post_id)

    like, created = Like.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        _create_notification(post.author, request.user, 'like', post)

    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'like_count': post.like_count,
        })

    # Redirect back to the page the user was on (feed, explore, or detail)
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('posts:detail', slug=post.slug)


@login_required
def comment_add_view(request, post_id):
    """Add a comment to a post."""
    post = get_object_or_404(Post, pk=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    parent_comment = Comment.objects.get(id=parent_id, post=post)
                    comment.parent = parent_comment
                except Comment.DoesNotExist:
                    pass

            comment.save()
            _create_notification(post.author, request.user, 'comment', post)
            messages.success(request, 'Comment added!')

    return redirect('posts:detail', slug=post.slug)


@login_required
def comment_edit_view(request, comment_id):
    """Edit a comment."""
    comment = get_object_or_404(Comment, pk=comment_id)

    if comment.author != request.user and not request.user.is_admin_role:
        messages.error(request, 'You cannot edit this comment.')
        return redirect('posts:detail', slug=comment.post.slug)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            messages.success(request, 'Comment updated!')

    return redirect('posts:detail', slug=comment.post.slug)


@login_required
def comment_delete_view(request, comment_id):
    """Delete a comment."""
    comment = get_object_or_404(Comment, pk=comment_id)

    if comment.author != request.user and not request.user.is_admin_role:
        messages.error(request, 'You cannot delete this comment.')
        return redirect('posts:detail', slug=comment.post.slug)


    if request.method == 'POST':
        slug = comment.post.slug
        comment.delete()
        messages.success(request, 'Comment deleted.')
        return redirect('posts:detail', slug=slug)

    return redirect('posts:detail', slug=comment.post.slug)


@login_required
def comment_like_toggle_view(request, comment_id):
    """Toggle like/unlike on a comment."""
    from .models import CommentLike
    comment = get_object_or_404(Comment, pk=comment_id)

    like, created = CommentLike.objects.get_or_create(comment=comment, user=request.user)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
        _create_notification(comment.author, request.user, 'like', comment.post)

    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'like_count': comment.likes.count(),
        })

    # Redirect back to the page the user was on
    referer = request.META.get('HTTP_REFERER')
    if referer:
        return redirect(referer)
    return redirect('posts:detail', slug=comment.post.slug)


@login_required
def follow_toggle_view(request, username):
    """Toggle follow/unfollow a user."""
    target_user = get_object_or_404(User, username=username)

    if request.user == target_user:
        messages.warning(request, "You can't follow yourself.")
        return redirect('users:profile', username=username)

    follow, created = Follow.objects.get_or_create(
        follower=request.user,
        following=target_user,
    )
    if not created:
        follow.delete()
        messages.info(request, f'You unfollowed {target_user.username}.')
    else:
        _create_notification(target_user, request.user, 'follow')
        messages.success(request, f'You are now following {target_user.username}!')

    return redirect('users:profile', username=username)


@login_required
def notifications_view(request):
    """Show all notifications for the logged-in user."""
    user_notifs = Notification.objects.filter(recipient=request.user)

    # Mark all unread as read and capture count before marking
    unread_count = user_notifs.filter(is_read=False).count()
    user_notifs.filter(is_read=False).update(is_read=True)

    # Now fetch the latest 50 for display
    notifications = user_notifs.select_related('actor', 'post')[:50]

    return render(request, 'interactions/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })


@login_required
def notification_mark_read(request, pk):
    """Mark a single notification as read (AJAX)."""
    notif = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notif.is_read = True
    notif.save()
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': True})
    return redirect('interactions:notifications')


@login_required
def note_add_view(request):
    """Create a new 24h note."""
    from .models import Note
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            if len(content) > 60:
                content = content[:60]
            note = Note.objects.create(user=request.user, content=content)
            messages.success(request, 'Your note has been shared.')
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                avatar_url = request.user.avatar.url if getattr(request.user, 'avatar', None) else None
                return JsonResponse({
                    'ok': True,
                    'note': {
                        'id': note.id,
                        'user': request.user.username,
                        'user_initial': request.user.username[0].upper() if request.user.username else 'U',
                        'avatar_url': avatar_url,
                        'content': note.content,
                        'created_at': 'just now'
                    }
                })
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'ok': False, 'error': 'Invalid note content.'}, status=400)
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer if referer else 'posts:home')
