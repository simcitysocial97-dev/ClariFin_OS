# Production Hardening Guide

## Overview

This document covers the production hardening improvements made to ClariFin_OS for reliable personal self-hosted use.

## Configuration

### Environment Variables

All configuration is centralized in `backend/src/config.py`. The following environment variables are supported:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_PATH` | `data/finance.db` | Path to SQLite database file |
| `UPLOAD_DIR` | `data/uploads` | Directory for uploaded files |
| `BACKEND_PORT` | `8000` | Backend server port |
| `FRONTEND_PORT` | `3000` | Frontend server port |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | API URL for frontend |
| `CORS_ORIGINS` | (localhost defaults) | Comma-separated allowed CORS origins |
| `LOG_LEVEL` | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `MAX_UPLOAD_SIZE_MB` | `50` | Maximum upload file size in MB |
| `ALLOWED_EXTENSIONS` | `.pdf,.csv,.xlsx,.xls` | Allowed file extensions |
| `ENABLE_ANALYTICS` | `true` | Enable analytics engine |
| `ENABLE_BEHAVIOR_ENGINE` | `true` | Enable behavior analysis engine |

### Configuration Validation

On startup, the application validates:
- Database directory is accessible/creatable
- Upload directory is accessible/creatable
- Port numbers are valid (1-65535)
- Log level is valid

## Error Handling

### Standardized Error Responses

All API errors return a consistent JSON structure:

```json
{
  "error": {
    "message": "Human-readable error message",
    "status_code": 400,
    "details": { ... }  // Optional additional context
  }
}
```

### Error Types

- `ValidationError` (400) - Input validation failures
- `NotFoundError` (404) - Resource not found
- `DatabaseError` (500) - Database operation failures
- `FileError` (400) - File operation failures
- `ImportError` (400) - Data import failures
- `AppError` (500) - Generic application errors

### Stack Trace Protection

Stack traces are only included in error responses when `LOG_LEVEL=DEBUG`. In production, only generic error messages are returned.

## Input Validation

### Monetary Values

- All amounts are validated as integers (paise)
- Range: ±₹99,99,99,999.99 (about 1 billion INR)
- Use `validate_paise_amount()` for validation

### Dates

- Supports multiple Indian date formats
- ISO format (YYYY-MM-DD) for API input
- Use `validate_iso_date()` for validation

### File Uploads

- Extension whitelist validation
- Size limit enforcement
- Path traversal protection
- Use `validate_file_upload()` for validation

## Logging

### Format

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

### Log Levels

- `DEBUG` - Detailed debugging information
- `INFO` - General operational messages
- `WARNING` - Warning conditions
- `ERROR` - Error conditions
- `CRITICAL` - Critical errors

### Request Logging

All requests are logged with:
- HTTP method
- Request path
- Response status code
- Additional context (when available)

## Database Reliability

### Transactions

- All database operations use context manager protocol
- Automatic commit on success, rollback on failure
- WAL mode enabled for better concurrency

### Integrity Constraints

- Foreign key constraints enabled
- Unique constraints on (bank, file_name) for statements
- Unique constraints on hash_signature for transactions
- Immutability triggers prevent transaction updates/deletes

### Connection Management

- Connections are properly closed after use
- Context manager support for automatic cleanup
- Row factory for dict-like row access

## Health & Diagnostics

### `/health` Endpoint

Returns 200 OK if the application is running. Lightweight check that doesn't verify database connectivity.

```bash
curl http://localhost:8000/health
```

### `/ready` Endpoint

Returns 200 OK if all systems are operational, 503 otherwise. Verifies:
- Database connectivity
- Upload directory accessibility

```bash
curl http://localhost:8000/ready
```

## Startup Validation

Run the startup validation script before starting the application:

```bash
python backend/src/startup.py
```

This validates:
- Configuration is valid
- Required directories exist/creatable
- Database is reachable (if exists)

## Security Hygiene

### Secrets Management

- All secrets should be stored in environment variables
- No hardcoded credentials in code
- `.env` file should be in `.gitignore`

### File Upload Security

- Extension whitelist validation
- Size limits enforced
- Files stored in dedicated upload directory
- No direct file access from web

### SQL Injection Prevention

- All queries use parameterized statements
- No string concatenation in SQL
- Input validation before database operations

### CORS Configuration

- Configurable allowed origins
- Defaults to localhost for development
- Credentials support enabled

## Backup Recommendations

### Database Backup

```bash
# Simple backup
cp data/finance.db backups/finance-$(date +%Y%m%d).db

# Automated backup script
#!/bin/bash
BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d-%H%M%S)
cp data/finance.db "$BACKUP_DIR/finance-$DATE.db"
# Keep last 30 days
find "$BACKUP_DIR" -name "finance-*.db" -mtime +30 -delete
```

### Backup Frequency

- Daily backups recommended
- Before major imports
- Before system updates

## Troubleshooting

### Common Issues

**Database not found**
- The database is created automatically on first use
- Check `DATABASE_PATH` environment variable

**Upload directory not accessible**
- Check `UPLOAD_DIR` environment variable
- Ensure parent directory exists and is writable

**CORS errors**
- Add your frontend URL to `CORS_ORIGINS`
- Restart the backend after changes

**Import validation failures**
- Check the `/api/audit/report` endpoint
- Review transaction counts and totals

### Log Analysis

Check logs for:
- ERROR level messages for failures
- WARNING level messages for potential issues
- Request patterns and response codes

## Deployment Notes

### Production Checklist

- [ ] Set `LOG_LEVEL=WARNING` or `ERROR`
- [ ] Configure `CORS_ORIGINS` for your domain
- [ ] Set `MAX_UPLOAD_SIZE_MB` appropriately
- [ ] Test `/health` and `/ready` endpoints
- [ ] Verify backup procedures
- [ ] Review file permissions on data directory

### Running the Application

```bash
# Backend
cd backend
python src/api.py

# Or with uvicorn directly
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

## Remaining Risks

1. **No automated backup** - Manual backup procedures required
2. **No file encryption** - Uploaded files stored in plain text
3. **No rate limiting** - Could be vulnerable to DoS attacks
4. **No request size limits** - Large requests could exhaust memory
5. **No authentication** - Designed for personal use, not multi-user

These risks are acceptable for personal self-hosted use but should be addressed for any shared deployment.