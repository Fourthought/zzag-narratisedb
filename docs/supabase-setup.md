# Local Supabase Setup

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — install and make sure it's running before proceeding
- [Supabase CLI](https://supabase.com/docs/guides/local-development/cli/getting-started) — install via Homebrew:
  ```bash
  brew install supabase/tap/supabase
  ```

---

## Setup

### 1. Login to Supabase

```bash
supabase login
```

This opens a browser to authenticate your CLI.

### 2. Link the project

```bash
supabase link --project-ref <project-ref>
```

Get the project ref from whoever manages the Supabase project, or from the dashboard URL:

```
https://supabase.com/dashboard/project/abcdefghijklmnop
                                        ^^^^^^^^^^^^^^^^
```

### 3. Start the local instance

```bash
supabase start
```

First run pulls Docker images — takes a few minutes. You'll see this output when ready:

```
API URL: http://127.0.0.1:54321
DB URL:  postgresql://postgres:postgres@127.0.0.1:54322/postgres
Studio:  http://127.0.0.1:54323
```

### 4. Seed local database with remote data

To populate your local DB with real data from the remote:

```bash
supabase db dump --data-only -f supabase/seed.sql
psql postgresql://postgres:postgres@127.0.0.1:54322/postgres < supabase/seed.sql
```

> `seed.sql` is gitignored — it contains real user data and should never be committed.

### 5. Configure environment variables

Add these to your `.env.local` (these will be different from the remote Supabase project and displayed after you run supabase start):

```env
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY=[generated_key]
```

---

## Daily Use

```bash
supabase start    # start local instance (Docker must be running)
supabase stop     # stop local instance
supabase db reset # rebuild local DB from migrations (run after pulling new migrations)
```

Local dashboard (Supabase Studio) available at `http://127.0.0.1:54323` when running.

---

## Keeping in Sync

When you pull new code that includes migrations, rebuild your local DB:

```bash
git pull
supabase db reset
```
