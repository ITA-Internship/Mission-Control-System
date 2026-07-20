## Deployment Workflow & CI/CD

This application uses Docker, Nginx, Gunicorn, Celery, and Redis. Deployment automation is handled via GitHub Actions.

### 1. Prerequisites & Environment Checks
Before deploying to any target environment, ensure the `.env` file is present and correctly populated.
Run the validation script to prevent runtime failures:
```bash
bash deploy/scripts/check_env.sh
```

### 2. Build Verification & Release Preparation
Our CI/CD pipeline automatically enforces quality via GitHub Actions:

Validation Steps: Linter (pre-commit) and Unit Tests run on all branches.

Build Verification: The Dockerfile is built in an isolated CI runner to guarantee it compiles before reaching the server.

### 3. Executing Deployment
To deploy changes to the target environment (can be triggered via CI/CD foundation or manually):

```bash
# 1. Pull the latest code
git pull origin main

# 2. Rebuild and restart the stack in the background
docker-compose up -d --build
```

### 4. Health Checks
The platform uses built-in Docker health checks. To confirm the application is healthy after deployment:

Run docker-compose ps.

Wait a few seconds and ensure the STATUS for web, nginx, db, and redis shows as (healthy).

Test the Nginx reverse proxy endpoint directly (it runs on port 8000 locally):

```bash
curl -I [http://127.0.0.1:8000/api/health/](http://127.0.0.1:8000/api/health/)
```

Expected result: HTTP 200 OK.

5. Rollback and Recovery Guidance
If the deployment fails validation or a container becomes (unhealthy), follow these recovery steps:

Check Logs: Identify the failure point (e.g., Gunicorn or Celery error):

```bash
docker-compose logs --tail=50 web celery
```

Rollback: If a code revert is necessary, stop the containers, checkout the previous stable commit, and redeploy:

```bash
docker-compose down
git checkout <previous-stable-commit-hash>
docker-compose up -d --build
```
