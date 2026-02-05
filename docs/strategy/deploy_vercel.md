# Deploy to Vercel (Resend email capture)

## Steps
1. Create a new Vercel project from this repo.
2. Add environment variable `RESEND_API_KEY`.
3. Deploy.

## Token-based auth (recommended)
```bash
export VERCEL_TOKEN=your_token
```

## Fast path (script)
```bash
./set_env.sh
```

## Manual env command (CLI)
```bash
vercel env add RESEND_API_KEY production
```

## One command deploy + open
```bash
./deploy.sh
```

## End-to-end test (local)
```bash
RESEND_API_KEY=your_key VERCEL_TOKEN=your_token RESEND_TO_EMAIL=you@domain.com ./e2e_test.sh
```

This will open the local page and save a screenshot to `site_screenshots/`.

## Test locally
```bash
# install Vercel CLI if needed
npm i -g vercel
vercel dev
```

Then visit `http://localhost:3000` and submit the email form.

## Endpoint
- `POST /api/lead`
- body: `{ "email": "you@company.com", "source": "landing" }`
