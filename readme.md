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

Create a `.env` file from `.env.example` and configure:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `DATABASE_URL`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

## Run Tests

```bash
python manage.py test
```

## Deployment

1. Push the project to GitHub.
2. Create a Railway project from the GitHub repository.
3. Configure environment variables.
4. Optional: add a Railway MySQL/Postgres service and set its `DATABASE_URL`.
5. Deploy. The `Procfile` runs migrations before starting Gunicorn.

Recommended Railway variables:

- `SECRET_KEY`
- `DEBUG=False`
- `ALLOWED_HOSTS=.railway.app,your-custom-domain.com`
- `CSRF_TRUSTED_ORIGINS=https://your-app.up.railway.app`
- `DATABASE_URL` if using Railway MySQL/Postgres
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`

## Notes

Do not commit `.env`, `db.sqlite3`, `media/`, `__pycache__/`, or virtual environment folders.
