import json

from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from interactions.models import Bookmark, Comment, Like
from posts.models import Category, Post, Tag


def _json_body(request):
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode('utf-8'))
    except json.JSONDecodeError:
        return None


def _post_payload(post, include_content=False):
    data = {
        'id': post.id,
        'title': post.title,
        'slug': post.slug,
        'excerpt': post.excerpt,
        'author': post.author.username,
        'category': post.category.name if post.category else None,
        'tags': [tag.name for tag in post.tags.all()],
        'like_count': getattr(post, 'num_likes', post.like_count),
        'comment_count': getattr(post, 'num_comments', post.comment_count),
        'created_at': post.created_at.isoformat(),
        'updated_at': post.updated_at.isoformat(),
    }
    if include_content:
        data['content'] = post.content
    return data


def _comment_payload(comment):
    return {
        'id': comment.id,
        'post': comment.post.slug,
        'author': comment.author.username,
        'parent_id': comment.parent_id,
        'content': comment.content,
        'like_count': comment.like_count,
        'created_at': comment.created_at.isoformat(),
    }


@require_http_methods(['GET', 'POST'])
def posts_api(request):
    if request.method == 'GET':
        posts = (
            Post.objects.filter(status=Post.Status.PUBLISHED)
            .select_related('author', 'category')
            .prefetch_related('tags')
            .annotate(num_likes=Count('likes'), num_comments=Count('comments'))
            .order_by('-created_at')
        )
        return JsonResponse({'results': [_post_payload(post) for post in posts]})

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required.'}, status=401)

    data = _json_body(request)
    if data is None:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    if not title or not content:
        return JsonResponse({'error': 'Title and content are required.'}, status=400)

    category = None
    category_slug = (data.get('category_slug') or '').strip()
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)

    post = Post.objects.create(
        title=title,
        content=content,
        excerpt=(data.get('excerpt') or '').strip(),
        category=category,
        author=request.user,
        status=Post.Status.PUBLISHED,
    )

    tag_names = data.get('tags') or []
    if isinstance(tag_names, list):
        tags = []
        for name in tag_names:
            clean_name = str(name).strip().lower().lstrip('#')
            if clean_name:
                tag, _ = Tag.objects.get_or_create(name=clean_name)
                tags.append(tag)
        post.tags.set(tags)

    return JsonResponse(_post_payload(post, include_content=True), status=201)


@require_http_methods(['GET', 'PATCH', 'DELETE'])
def post_detail_api(request, slug):
    post = get_object_or_404(
        Post.objects.select_related('author', 'category').prefetch_related('tags'),
        slug=slug,
        status=Post.Status.PUBLISHED,
    )

    if request.method == 'GET':
        return JsonResponse(_post_payload(post, include_content=True))

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required.'}, status=401)

    if post.author != request.user and not request.user.is_admin_role:
        return JsonResponse({'error': 'You can only change your own posts.'}, status=403)

    if request.method == 'DELETE':
        post.delete()
        return JsonResponse({'deleted': True})

    data = _json_body(request)
    if data is None:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    for field in ['title', 'content', 'excerpt']:
        if field in data:
            setattr(post, field, str(data[field]).strip())
    post.save()
    return JsonResponse(_post_payload(post, include_content=True))


@require_http_methods(['GET', 'POST'])
def post_comments_api(request, slug):
    post = get_object_or_404(Post, slug=slug, status=Post.Status.PUBLISHED)

    if request.method == 'GET':
        comments = post.comments.select_related('author').order_by('-created_at')
        return JsonResponse({'results': [_comment_payload(comment) for comment in comments]})

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required.'}, status=401)

    data = _json_body(request)
    if data is None:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    content = (data.get('content') or '').strip()
    if not content:
        return JsonResponse({'error': 'Content is required.'}, status=400)

    parent = None
    parent_id = data.get('parent_id')
    if parent_id:
        parent = get_object_or_404(Comment, id=parent_id, post=post)

    comment = Comment.objects.create(
        post=post,
        author=request.user,
        parent=parent,
        content=content,
    )
    return JsonResponse(_comment_payload(comment), status=201)


@require_POST
def post_like_api(request, slug):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required.'}, status=401)

    post = get_object_or_404(Post, slug=slug, status=Post.Status.PUBLISHED)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    if not created:
        like.delete()
    return JsonResponse({
        'liked': created,
        'like_count': post.likes.count(),
    })


@require_http_methods(['GET', 'POST'])
def bookmarks_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Login required.'}, status=401)

    if request.method == 'GET':
        bookmarks = (
            Bookmark.objects.filter(user=request.user)
            .select_related('post', 'post__author', 'post__category')
            .prefetch_related('post__tags')
        )
        return JsonResponse({
            'results': [_post_payload(bookmark.post) for bookmark in bookmarks]
        })

    data = _json_body(request)
    if data is None:
        return JsonResponse({'error': 'Invalid JSON.'}, status=400)

    slug = (data.get('slug') or '').strip()
    post = get_object_or_404(Post, slug=slug, status=Post.Status.PUBLISHED)
    bookmark, created = Bookmark.objects.get_or_create(post=post, user=request.user)
    if not created:
        bookmark.delete()
    return JsonResponse({
        'bookmarked': created,
        'bookmark_count': post.bookmarks.count(),
    })
