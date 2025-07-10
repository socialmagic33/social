# LeadMagic API

Backend API for LeadMagic - Social automation tool for contractors, builders, and service pros.

## Architecture

This is a **pure FastAPI backend API** that provides:

- RESTful API endpoints for all functionality
- JWT-based authentication
- Media upload and processing
- AI-powered content generation
- Social media integration
- Post scheduling and automation

## Frontend Options

This API can be consumed by any frontend framework:

- **React/Next.js** - Modern SPA or SSR
- **Vue.js/Nuxt** - Progressive web app
- **Mobile Apps** - React Native, Flutter, native iOS/Android
- **Desktop Apps** - Electron, Tauri

## Development Setup

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis
- Docker (optional)

### Local Development

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy `.env.example` to `.env` and configure:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run database migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the development server:
   ```bash
   npm run dev
   # or
   uvicorn app.main:app --reload
   ```

7. Visit http://localhost:8000/docs for API documentation

### Docker Development

```bash
docker-compose up -d
```

This starts:
- API server on http://localhost:8000
- PostgreSQL on localhost:5432
- Redis on localhost:6379
- Celery worker for background tasks

## API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Key Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/refresh` - Refresh access token

### Media Management
- `POST /api/media/upload` - Upload media files
- `GET /api/media` - List user's media
- `GET /api/media/{media_id}` - Get specific media

### Jobsite Management
- `POST /api/jobsites` - Create jobsite
- `GET /api/jobsites` - List user's jobsites
- `GET /api/jobsites/{jobsite_id}` - Get jobsite details

### Post Management
- `GET /api/posts/unpublished` - List unpublished posts
- `POST /api/posts/schedule` - Schedule posts
- `POST /api/posts/process-media/{jobsite_id}` - Process jobsite media

### AI Services
- `POST /api/ai/generate-caption/{grouping_id}` - Generate AI captions

### Social Media
- `GET /api/social/meta/auth` - Connect Meta accounts
- `GET /api/social/accounts` - List connected accounts

## Deployment

### Production Environment Variables

```bash
DATABASE_URL=postgresql://user:password@host:5432/leadmagic
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
EMAIL_FROM=noreply@example.com
BASE_URL=https://api.leadmagic.com

# AWS S3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
AWS_BUCKET_NAME=your-bucket-name

# Redis
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password

# Meta API
META_APP_ID=your-meta-app-id
META_APP_SECRET=your-meta-app-secret

# Monitoring
SENTRY_DSN=your-sentry-dsn
```

### Docker Production

```bash
docker build -t leadmagic-api .
docker run -p 8000:8000 --env-file .env leadmagic-api
```

### Cloud Deployment

This API can be deployed to:

- **Railway** - Easy Python deployment
- **Render** - Simple web services
- **DigitalOcean App Platform** - Managed containers
- **AWS ECS/Fargate** - Scalable containers
- **Google Cloud Run** - Serverless containers
- **Heroku** - Traditional PaaS

## Testing

```bash
# Run tests
npm run test
# or
pytest

# Run with coverage
pytest --cov=app tests/

# Lint code
npm run lint
# or
flake8 app tests

# Format code
npm run format
# or
black app tests
```

## Monitoring

- **Health Check**: `GET /health`
- **Metrics**: `GET /metrics` (Prometheus format)
- **Error Tracking**: Sentry integration
- **Logging**: Structured JSON logs

## Security

- JWT-based authentication
- Rate limiting on all endpoints
- CORS protection
- Input validation with Pydantic
- SQL injection protection with SQLAlchemy
- File upload validation
- CSRF protection for state-changing operations

## Background Tasks

Uses Celery with Redis for:
- Media processing
- Email sending
- Social media posting
- Scheduled tasks

Start worker:
```bash
celery -A app.worker worker --loglevel=info
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Run linting and tests
6. Submit a pull request

## License

Private - All rights reserved