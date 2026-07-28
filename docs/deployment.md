## Deployment Workflow & CI/CD

This application uses Docker, Nginx, Gunicorn, Celery, Redis, and PostgreSQL.
Deployment automation and validation are handled through GitHub Actions.

### 1. Prerequisites & Environment Checks

Before deploying to any target environment, ensure the `.env` file is present
and correctly populated.

Run the environment validation script to prevent runtime failures and insecure
production configuration:

```bash
bash deploy/scripts/check_env.sh
```

Run the Django deployment security checks against the production
configuration:

```bash
python manage.py check --deploy --tag security --fail-level WARNING
```

The deployment check must complete without warnings before the application is
deployed.

The production environment must include:

```env
DEBUG=False

ALLOWED_HOSTS=api.example.com
CSRF_TRUSTED_ORIGINS=https://api.example.com

# Host header used by internal Docker health checks.
# It must match one of the values in ALLOWED_HOSTS.
HEALTHCHECK_HOST=api.example.com

SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True

SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

Do not include `http://`, `https://`, ports, or URL paths in
`ALLOWED_HOSTS` or `HEALTHCHECK_HOST`.

### 2. Build Verification & Release Preparation

The CI/CD pipeline automatically runs validation through GitHub Actions.

The pipeline includes:

* pre-commit and linting checks;
* unit tests;
* Django deployment security checks;
* Docker image build verification.

The Dockerfile is built in an isolated CI runner to confirm that the
application image can be created before deployment.

### 3. Executing Deployment

To deploy changes to the target environment:

```bash
# 1. Pull the latest code
git pull origin main

# 2. Rebuild and restart the stack
docker compose up -d --build
```

Verify the running containers:

```bash
docker compose ps
```

### 4. HTTPS Termination

Production deployments must use HTTPS for all public traffic.

The recommended deployment topology is:

```text
Client
  -> HTTPS load balancer or reverse proxy
  -> Nginx
  -> Gunicorn
  -> Django
```

TLS must be terminated by a trusted external load balancer or reverse proxy.

The production network must provide:

* an HTTPS listener on port `443` with a valid TLS certificate;
* an HTTP listener on port `80` that redirects all requests to HTTPS;
* removal of any client-provided `X-Forwarded-Proto` header;
* `X-Forwarded-Proto: https` for requests received over HTTPS;
* private-only access from the trusted proxy to the bundled Nginx listener.

Do not expose the bundled Nginx listener directly to the public internet.

For the initial HSTS rollout, use a short duration:

```env
SECURE_HSTS_SECONDS=3600
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
```

Increase the HSTS duration and enable `includeSubDomains` and `preload` only
after confirming that the main domain, every subdomain, and all external
resources work correctly over HTTPS.

Verify the HTTP-to-HTTPS redirect:

```bash
curl -I http://api.example.com/api/health/
```

Expected response:

```text
HTTP/1.1 301 Moved Permanently
Location: https://api.example.com/api/health/
```

A `308 Permanent Redirect` response is also valid.

Verify the HTTPS endpoint and HSTS header:

```bash
curl -I https://api.example.com/api/health/
```

Expected response headers include:

```text
HTTP/1.1 200 OK
Strict-Transport-Security: max-age=31536000; includeSubDomains; preload
```

Verify that authentication cookies contain the required security attributes:

```text
sessionid=...; HttpOnly; Secure; SameSite=Lax
csrftoken=...; Secure; SameSite=Lax
```

### 5. Health Checks

The platform uses built-in Docker health checks.

Check the status of all containers:

```bash
docker compose ps
```

Wait until the following services are running and healthy:

```text
web
nginx
db
redis
```

Test the local Nginx reverse proxy endpoint:

```bash
curl -I http://127.0.0.1:8000/api/health/
```

Expected local result:

```text
HTTP/1.1 200 OK
```

Validate the Nginx configuration:

```bash
docker compose exec nginx nginx -t
```

Expected result:

```text
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

### 6. Rollback and Recovery Guidance

If deployment validation fails or a container becomes unhealthy, check the
application logs:

```bash
docker compose logs --tail=100 web celery nginx
```

To roll back to a previous stable version:

```bash
# 1. Stop the current containers
docker compose down

# 2. Check out the previous stable commit
git checkout <previous-stable-commit-hash>

# 3. Rebuild and restart the stack
docker compose up -d --build
```

After rollback, repeat the environment validation, deployment security checks,
container health checks, and HTTPS verification.
