# GitHub upload guide

## 1. Personalize the repository

Before publishing, update:

- The copyright holder in `LICENSE`
- The project author in your GitHub repository description
- Demo links after deployment
- Resume bullets in `README.md` with your actual measured test coverage and load-test results

Never claim results you did not measure.

## 2. Create the Git repository

```bash
git init
git add .
git commit -m "feat: build SeatSync concurrent ticket-booking platform"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/seatsync.git
git push -u origin main
```

## 3. Recommended GitHub settings

Repository description:

> Concurrent ticket-booking backend with atomic seat locks, idempotent payments, state-machine booking flows, Docker and CI.

Topics:

```text
fastapi python postgresql redis sqlalchemy system-design lld
concurrency distributed-systems backend docker pytest
```

Enable:

- GitHub Actions
- Dependabot alerts
- Branch protection on `main`
- Secret scanning

## 4. Add screenshots

After running the project, add these to `docs/images/`:

1. `/demo` interface
2. Swagger API page
3. Successful booking response
4. Concurrency race demonstration
5. Test coverage output

Reference them near the top of the README.

## 5. Deployment

A simple deployment requires:

- Web service running the Dockerfile
- Managed PostgreSQL database
- Managed Redis instance
- Environment variables from `.env.example`
- A strong random `JWT_SECRET`

Run database migrations during release/startup. Do not expose the demo admin
credentials on a public deployment.

## 6. Final verification

```bash
python -m compileall -q app scripts tests
pytest --cov=app --cov-report=term-missing
docker compose config
docker compose up --build
```

Then manually complete one successful payment and one failed payment through
Swagger or `/demo`.
