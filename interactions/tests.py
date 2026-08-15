import json
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from interactions.models import Bookmark, Comment, Follow, Like
from posts.models import Post
from posts.models import Tag
from users.models import EmailOTP, User


@override_settings(
    ALLOWED_HOSTS=['testserver'],
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage',
)
class CoreFlowTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='StrongPass123',
            role=User.Role.AUTHOR,
        )
        self.reader = User.objects.create_user(
            username='reader',
            email='reader@example.com',
            password='StrongPass123',
        )
        self.post = Post.objects.create(
            title='First Post',
            content='This is a useful post for testing.',
            author=self.author,
            status=Post.Status.PUBLISHED,
        )

    def test_registration_creates_inactive_user_then_otp_activates_it(self):
        response = self.client.post(reverse('users:register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })

        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username='newuser')
        self.assertFalse(user.is_active)

        otp = EmailOTP.objects.get(email='new@example.com')
        response = self.client.post(reverse('users:verify_otp'), {'otp': otp.otp})

        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    @override_settings(ALLOW_DEMO_OTP_FALLBACK=True)
    @patch('users.views.send_mail', side_effect=OSError('Network is unreachable'))
    def test_registration_shows_demo_otp_when_email_fails(self, _send_mail):
        response = self.client.post(reverse('users:register'), {
            'username': 'demo_user',
            'email': 'demo@example.com',
            'password1': 'StrongPass123',
            'password2': 'StrongPass123',
        })

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('users:verify_otp'))
        user = User.objects.get(username='demo_user')
        self.assertFalse(user.is_active)
        self.assertEqual(self.client.session['demo_otp_code'], EmailOTP.objects.get(email='demo@example.com').otp)

    def test_author_can_create_edit_and_delete_post_via_api(self):
        self.client.force_login(self.reader)
        create_response = self.client.post(
            reverse('api_posts'),
            data=json.dumps({'title': 'API Post', 'content': 'Created from API.'}),
            content_type='application/json',
        )

        self.assertEqual(create_response.status_code, 201)
        slug = create_response.json()['slug']

        patch_response = self.client.patch(
            reverse('api_post_detail', args=[slug]),
            data=json.dumps({'title': 'Updated API Post'}),
            content_type='application/json',
        )

        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()['title'], 'Updated API Post')

        delete_response = self.client.delete(reverse('api_post_detail', args=[slug]))
        self.assertEqual(delete_response.status_code, 200)
        self.assertFalse(Post.objects.filter(slug=slug).exists())

    def test_non_author_cannot_edit_post_via_api(self):
        self.client.force_login(self.reader)
        response = self.client.patch(
            reverse('api_post_detail', args=[self.post.slug]),
            data=json.dumps({'title': 'Not allowed'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 403)

    def test_like_toggle_api(self):
        self.client.force_login(self.reader)
        url = reverse('api_post_like', args=[self.post.slug])

        liked_response = self.client.post(url)
        self.assertEqual(liked_response.status_code, 200)
        self.assertTrue(liked_response.json()['liked'])
        self.assertEqual(Like.objects.count(), 1)

        unliked_response = self.client.post(url)
        self.assertFalse(unliked_response.json()['liked'])
        self.assertEqual(Like.objects.count(), 0)

    def test_like_toggle_view_returns_ajax_count(self):
        self.client.force_login(self.reader)
        response = self.client.post(
            reverse('interactions:like_toggle', args=[self.post.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'liked': True, 'like_count': 1})

    def test_home_tag_filter_loads_for_authenticated_user(self):
        tag = Tag.objects.create(name='onepiece')
        self.post.tags.add(tag)
        self.client.force_login(self.reader)

        response = self.client.get(reverse('posts:home'), {'tag': tag.slug})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.post.title)

    def test_profile_edit_saves_names_and_avatar(self):
        self.client.force_login(self.reader)
        avatar = SimpleUploadedFile(
            'avatar.gif',
            b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00\xff\xff\xff,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02L\x01\x00;',
            content_type='image/gif',
        )

        with TemporaryDirectory() as media_root:
            with override_settings(MEDIA_ROOT=media_root):
                response = self.client.post(reverse('users:profile_edit'), {
                    'first_name': 'Ved',
                    'last_name': 'Patel',
                    'bio': 'error dev',
                    'website': 'https://example.com',
                    'avatar': avatar,
                })

                self.assertEqual(response.status_code, 302)
                self.reader.refresh_from_db()
                self.assertEqual(self.reader.first_name, 'Ved')
                self.assertEqual(self.reader.last_name, 'Patel')
                self.assertEqual(self.reader.bio, 'error dev')
                self.assertEqual(self.reader.website, 'https://example.com')
                self.assertTrue(self.reader.avatar.name.startswith('avatars/'))

    def test_comment_api_adds_comment(self):
        self.client.force_login(self.reader)
        response = self.client.post(
            reverse('api_post_comments', args=[self.post.slug]),
            data=json.dumps({'content': 'Nice article.'}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Comment.objects.get().content, 'Nice article.')

    def test_bookmark_api_toggles_saved_post(self):
        self.client.force_login(self.reader)
        response = self.client.post(
            reverse('api_bookmarks'),
            data=json.dumps({'slug': self.post.slug}),
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['bookmarked'])
        self.assertEqual(Bookmark.objects.count(), 1)

        response = self.client.post(
            reverse('api_bookmarks'),
            data=json.dumps({'slug': self.post.slug}),
            content_type='application/json',
        )

        self.assertFalse(response.json()['bookmarked'])
        self.assertEqual(Bookmark.objects.count(), 0)

    def test_follow_toggle_view(self):
        self.client.force_login(self.reader)
        response = self.client.post(reverse('interactions:follow_toggle', args=[self.author.username]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(Follow.objects.filter(follower=self.reader, following=self.author).exists())
