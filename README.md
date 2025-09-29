# GitHub Issues Gateway Service

A FastAPI-based microservice that wraps the GitHub REST API for issue management and webhook handling with comprehensive non-functional requirements implementation.

## Authors
- **Aditya Shahari** 
- **Mohsen Minai** 
- **Pratham Pravin Gala**
- **Pranjal Shrivastava**

## Features

- **CRUD Operations**: Create, read, update, and close GitHub issues
- **Comment Management**: Add comments to existing issues
- **Webhook Processing**: Handle GitHub webhooks with signature verification
- **Security**: HMAC SHA-256 signature validation for webhooks
- **Idempotency**: Prevent duplicate webhook processing
- **Rate Limiting**: Respect GitHub API rate limits with backoff
- **Pagination**: Forward GitHub's pagination headers and Link metadata
- **Structured Logging**: JSON-formatted logs for observability
- **Health Monitoring**: Built-in health check endpoint

## Installation & Running

### Local Development

```bash
# Clone repository
git clone <https://github.com/adityashahari1/github-service.gitl>
cd github-service

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env
# Edit .env with your values

# Run application
uvicorn src.main:app --reload --port 8080
```

## API Documentation

Once running, visit:
- **Interactive Docs**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/healthz


## Error Handling

The service maps GitHub API errors to appropriate HTTP responses:

- **400 Bad Request**: Invalid input data or malformed requests
- **401 Unauthorized**: GitHub authentication failed or invalid webhook signature
- **404 Not Found**: Issue or repository not found
- **429 Too Many Requests**: Rate limit exceeded (includes Retry-After header)
- **503 Service Unavailable**: GitHub API unavailable or network errors


## Citations and External Dependencies

### **Main Application** (`src/main.py`)
- [FastAPI Framework](https://fastapi.tiangolo.com/) - Web framework and API documentation
- [GitHub REST API](https://docs.github.com/en/rest) - API endpoints and authentication
- [Python httpx library](https://www.python-httpx.org/) - HTTP client implementation
- [Pydantic models](https://docs.pydantic.dev/latest/) - Data validation and serialization
- [python-dotenv](https://pypi.org/project/python-dotenv/) - Environment variable management

### **Security Module** (`src/utils/security.py`)
- [GitHub Webhooks Security](https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries) - HMAC signature verification
- [Python hmac library](https://docs.python.org/3/library/hmac.html) - Cryptographic hashing
- [Python hashlib library](https://docs.python.org/3/library/hashlib.html) - SHA-256 implementation

### **Idempotency Module** (`src/utils/idempotency.py`)
- [Python hashlib library](https://docs.python.org/3/library/hashlib.html) - Hash generation for unique IDs
- [Python datetime library](https://docs.python.org/3/library/datetime.html) - Timestamp handling

### **Rate Limiting Module** (`src/utils/rate_limiter.py`)
- [GitHub Rate Limiting](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) - Rate limit header specifications
- [Python asyncio library](https://docs.python.org/3/library/asyncio.html) - Asynchronous delay implementation
- [FastAPI HTTPException](https://fastapi.tiangolo.com/tutorial/handling-errors/) - Error response handling

### **Pagination Module** (`src/utils/pagination.py`)
- [GitHub Pagination](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api) - Pagination semantics
- [HTTP Link Headers RFC 5988](https://tools.ietf.org/html/rfc5988) - Link header specification

### **Logging Module** (`src/utils/logging_utils.py`)
- [Python logging library](https://docs.python.org/3/library/logging.html) - Logging framework
- [12-Factor App Logs](https://12factor.net/logs) - Structured logging principles
- [Python datetime library](https://docs.python.org/3/library/datetime.html) - Timestamp formatting