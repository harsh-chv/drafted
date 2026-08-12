from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from users.models import User
from django.core.paginator import Paginator
from django.conf import settings
from .models import Post, Category, Tag
from .forms import PostForm
from interactions.forms import CommentForm
from interactions.models import Like


@login_required
def home_view(request):
    """Home page with blog listing, search, and filters."""
    posts = Post.objects.filter(status='published').select_related('author', 'category')

    # ── Search ──
    query = request.GET.get('q', '').strip()
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(author__username__icontains=query)
        )

    # ── Filter by category ──
    category_slug = request.GET.get('category', '')
    if category_slug:
        posts = posts.filter(category__slug=category_slug)

    # ── Filter by author ──
    author_name = request.GET.get('author', '')
    if author_name:
        posts = posts.filter(author__username=author_name)

    # ── Filter by tag ──
    tag_slug = request.GET.get('tag', '')
    if tag_slug:
        posts = posts.filter(tags__slug=tag_slug)

    # ── Sorting & Tabs ──
    sort = request.GET.get('sort', 'for_you')
    
    if sort == 'following' and request.user.is_authenticated:
        # Get users that current user follows
        following_ids = request.user.following.values_list('following_id', flat=True)
        posts = posts.filter(author_id__in=following_ids)
        posts = posts.order_by('-created_at')
    elif sort == 'popular':
        posts = posts.annotate(num_likes=Count('likes')).order_by('-num_likes')
    elif sort == 'oldest':
        posts = posts.order_by('created_at')
    elif sort == 'latest':
        posts = posts.order_by('-created_at')
    else:
        # Default 'For You' - show all latest posts
        posts = posts.order_by('-created_at')
        sort = 'for_you'

    # ── Pagination ──
    per_page = getattr(settings, 'POSTS_PER_PAGE', 9)
    paginator = Paginator(posts, per_page)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Sidebar data
    categories = Category.objects.annotate(num_posts=Count('posts')).order_by('-num_posts')
    featured_posts = Post.objects.filter(status='published', featured=True)[:5]
    tags = Tag.objects.annotate(num_posts=Count('posts')).order_by('-num_posts')[:20]

    # Get posts the current user has liked (for heart icon state)
    liked_post_ids = set()
    if request.user.is_authenticated:
        liked_post_ids = set(
            Like.objects.filter(user=request.user, post__in=page_obj.object_list)
            .values_list('post_id', flat=True)
        )

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'featured_posts': featured_posts,
        'tags': tags,
        'query': query,
        'current_category': category_slug,
        'current_tag': tag_slug,
        'current_sort': sort,
        'liked_post_ids': liked_post_ids,
    }
    return render(request, 'posts/home.html', context)


def post_detail_view(request, slug):
    """Blog post detail page with comments."""
    post = get_object_or_404(
        Post.objects.select_related('author', 'category'),
        slug=slug,
        status='published',
    )

    # Check if current user liked
    user_has_liked = False
    if request.user.is_authenticated:
        user_has_liked = Like.objects.filter(post=post, user=request.user).exists()

    # Comments
    comments = post.comments.filter(parent__isnull=True).select_related('author').order_by('-created_at')
    comment_form = CommentForm()

    # Pre-fetch liked comments to avoid N+1
    liked_comment_ids = []
    if request.user.is_authenticated:
        from interactions.models import CommentLike
        liked_comment_ids = list(CommentLike.objects.filter(user=request.user).values_list('comment_id', flat=True))

    # Related posts
    related_posts = Post.objects.filter(
        status='published',
        category=post.category,
    ).exclude(pk=post.pk)[:4]

    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'user_has_liked': user_has_liked,
        'related_posts': related_posts,
        'liked_comment_ids': liked_comment_ids,
    }
    return render(request, 'posts/detail.html', context)


@login_required
def post_create_view(request):
    """Create a new blog post. Any authenticated user can write."""
    # Auto-upgrade Reader to Author on first post creation
    if request.user.role == 'reader':
        request.user.role = 'author'
        request.user.save(update_fields=['role'])

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            # Ensure post is published (not stuck as draft)
            if not post.status:
                post.status = 'published'
            post.save()
            form._save_tags(post)
            messages.success(request, 'Post published successfully!')
            return redirect('posts:detail', slug=post.slug)
        else:
            # Show form errors in a toast
            for field, errors in form.errors.items():
                for error in errors:
                    field_name = form.fields[field].label or field.replace('_', ' ').title() if field in form.fields else field
                    messages.error(request, f'{field_name}: {error}')
    else:
        form = PostForm()

    return render(request, 'posts/post_form.html', {
        'form': form,
        'title': 'Create Post',
    })


@login_required
def post_edit_view(request, slug):
    """Edit an existing blog post."""
    post = get_object_or_404(Post, slug=slug)

    # Only author or admin can edit
    if post.author != request.user and not request.user.is_admin_role:
        messages.error(request, 'You do not have permission to edit this post.')
        return redirect('posts:detail', slug=post.slug)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            form._save_tags(post)
            messages.success(request, 'Post updated successfully!')
            return redirect('posts:detail', slug=post.slug)
    else:
        form = PostForm(instance=post)

    return render(request, 'posts/post_form.html', {
        'form': form,
        'title': 'Edit Post',
        'post': post,
    })


@login_required
def post_delete_view(request, slug):
    """Delete a blog post."""
    post = get_object_or_404(Post, slug=slug)

    if post.author != request.user and not request.user.is_admin_role:
        messages.error(request, 'You do not have permission to delete this post.')
        return redirect('posts:detail', slug=post.slug)

    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully.')
        return redirect('posts:home')

    return render(request, 'posts/post_confirm_delete.html', {'post': post})


def category_view(request, slug):
    """View all posts in a category."""
    category = get_object_or_404(Category, slug=slug)
    posts = Post.objects.filter(status='published', category=category)

    paginator = Paginator(posts, getattr(settings, 'POSTS_PER_PAGE', 9))
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'posts/category.html', {
        'category': category,
        'page_obj': page_obj,
    })


def explore_view(request):
    """Explore / Discover page — search-centric with categories and trending."""
    posts = Post.objects.filter(status='published').select_related('author', 'category')

    # ── Search ──
    query = request.GET.get('q', '').strip()
    if query:
        posts = posts.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query) |
            Q(author__username__icontains=query)
        )

    # ── Filter by category ──
    category_slug = request.GET.get('category', '')
    if category_slug:
        posts = posts.filter(category__slug=category_slug)

    # ── Filter by tag ──
    tag_slug = request.GET.get('tag', '')
    if tag_slug:
        posts = posts.filter(tags__slug=tag_slug)

    # ── Sort ──
    sort = request.GET.get('sort', 'popular')
    if sort == 'latest':
        posts = posts.order_by('-created_at')
    else:
        posts = posts.annotate(num_likes=Count('likes')).order_by('-num_likes', '-created_at')
        sort = 'popular'

    # ── Pagination ──
    per_page = getattr(settings, 'POSTS_PER_PAGE', 9)
    paginator = Paginator(posts, per_page)
    page_obj = paginator.get_page(request.GET.get('page'))

    # Sidebar / discovery data
    categories = Category.objects.annotate(num_posts=Count('posts')).order_by('-num_posts')
    tags = Tag.objects.annotate(num_posts=Count('posts')).order_by('-num_posts')[:20]

    # Trending tags — top 5 tags with most posts, only those with at least 1 post
    trending_tags = Tag.objects.annotate(
        num_posts=Count('posts', filter=Q(posts__status='published'))
    ).filter(num_posts__gt=0).order_by('-num_posts')[:5]

    # Who to follow suggestions — users the current user does NOT follow
    suggested_users = []
    if request.user.is_authenticated:
        following_ids = list(
            request.user.following.values_list('following_id', flat=True)
        )
        following_ids.append(request.user.id)  # exclude self
        suggested_users = User.objects.exclude(
            id__in=following_ids
        ).annotate(
            num_posts=Count('posts', filter=Q(posts__status='published'))
        ).filter(num_posts__gt=0).order_by('-num_posts')[:5]

    # Get posts the current user has liked (for heart icon state)
    liked_post_ids = set()
    if request.user.is_authenticated:
        liked_post_ids = set(
            Like.objects.filter(user=request.user, post__in=page_obj.object_list)
            .values_list('post_id', flat=True)
        )

    context = {
        'page_obj': page_obj,
        'categories': categories,
        'tags': tags,
        'trending_tags': trending_tags,
        'suggested_users': suggested_users,
        'query': query,
        'current_category': category_slug,
        'current_tag': tag_slug,
        'current_sort': sort,
        'liked_post_ids': liked_post_ids,
    }
    return render(request, 'posts/explore.html', context)

