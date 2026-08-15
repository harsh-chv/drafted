# Drafted

Drafted is a Django blogging and social platform where users can publish posts, follow writers, comment on posts, like content, receive notifications, and save posts as bookmarks.

## Features

- Email OTP registration and login
- Google OAuth support through django-allauth
- Create, edit, delete, search, and filter blog posts
- Categories and tags
- Likes, nested comments, follows, notifications, and 24-hour notes
- Bookmarks / saved posts
- Basic JSON API for posts, comments, likes, and bookmarks
- Responsive Twitter/X-inspired interface with dark mode

## Tech Stack

- Backend: Django 4.2
- Database: MySQL in production, SQLite for local testing
- Auth: Django auth and django-allauth
- Frontend: Django templates, Tailwind CDN, custom CSS
- Deployment: Railway, Gunicorn, WhiteNoise

## API Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/posts/` | List published posts |
| POST | `/api/posts/` | Create a post |
| GET | `/api/posts/<slug>/` | Get post details |
| PATCH | `/api/posts/<slug>/` | Update own post |
| DELETE | `/api/posts/<slug>/` | Delete own post |
| GET | `/api/posts/<slug>/comments/` | List post comments |
| POST | `/api/posts/<slug>/comments/` | Add a comment |
| POST | `/api/posts/<slug>/like/` | Toggle like |
| GET | `/api/bookmarks/` | List saved posts |
| POST | `/api/bookmarks/` | Toggle bookmark |

## Setup

```bash
python -m venv myenv
myenv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

For macOS/Linux, use:

```bash
source myenv/bin/activate
cp .env.example .env
```

## Environment Variables

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `SERVE_MEDIA_FILES`
- `CLOUDINARY_URL`
- `DATABASE_URL`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `ALLOW_DEMO_OTP_FALLBACK`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

`ALLOW_DEMO_OTP_FALLBACK=True` is useful for portfolio/demo deployments where SMTP is blocked by the host. For a real production app, use a reliable email provider and set `ALLOW_DEMO_OTP_FALLBACK=False`.

Set `CLOUDINARY_URL` on Railway to make uploaded post images persistent across redeploys. Without Cloudinary, Railway can lose uploaded media after redeploy because its filesystem is temporary.

`SERVE_MEDIA_FILES=True` lets Django serve local uploaded images for a portfolio demo, but Cloudinary is the better fix for Railway.

## Run Tests

```bash
python manage.py test
```

## Deployment

1. Push the project to GitHub.
2. Create a Railway project from the GitHub repository.
3. Set `DEBUG=False`.
4. Set `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` for your Railway domain.
5. Add `DATABASE_URL` if using a Railway database service.
6. Add `CLOUDINARY_URL` for persistent image uploads.
7. Deploy. The `Procfile` runs migrations before starting Gunicorn.
