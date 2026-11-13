# Siteshelf

Upload a CSV / Excel file of websites (`website name`, `website link`, `website type`, `country`) and load it into PostgreSQL.

- **New website** -&gt; inserted (`created_at` and `updated_at` set automatically, UTC).
- **Website already in the table** -&gt; only `updated_at` is refreshed. Name, type, country and `created_at` stay as they are.
- **Duplicates inside the file** -&gt; collapsed to one row (last one wins).
- **Invalid rows** (missing fields, type not VC / PE / HNI, link without a domain, over-long values) -&gt; not loaded; shown with the file row number and the reason.

`website_id` is never supplied by the user. It is a hash of the normalized link (`https://www.Example.com/` and `example.com` give the same id), so the same site always maps to the same row.

## Layout

```
app/
  core/          config (env), database (engine/session), exceptions, logging, constants
  models/        SQLAlchemy ORM models           (Website)
  schemas/       Pydantic request/response models (API contract)
  repositories/  SQL only                        (upsert_many)
  services/      business logic                  (file_parser, validation, upload_service)
  utils/         pure helpers                    (urls: normalize + website_id)
  api/           FastAPI routes + dependencies   (/health, /api/v1/websites/upload)
  main.py        FastAPI app factory
ui/              Streamlit page (calls the same services as the API)
streamlit_app.py Streamlit entry point
tests/           pytest
```

Rule of thumb: routes and the Streamlit page stay thin and call **services**; services hold the rules and call **repositories**; only repositories talk SQL. A new feature (list/search sites, export, auth, background jobs) is a new route/page + service function + repository function.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate      # Python 3.10+
pip install -r requirements.txt
cp .env.example .env                                   # then fill in the DB_* values
```

### Database

Verify the existing database target (this only checks `website.website_info` and does not create or modify database objects):

```bash
python -m app.core.init_db
```

Existing `websites` table (from the earlier script), bring it in line with this version:

```sql
ALTER TABLE websites RENAME COLUMN country_code TO country;   -- skip if already renamed
ALTER TABLE websites ALTER COLUMN country TYPE VARCHAR(100);
```

Existing `website_id` values stay valid: the id function is unchanged.

## Run

```bash
streamlit run streamlit_app.py          # UI  -> http://localhost:8501
uvicorn app.main:app --reload           # API -> http://127.0.0.1:8000/docs
```

API example:

```bash
curl -F "file=@websites.xlsx" http://127.0.0.1:8000/api/v1/websites/upload
```

## Deploy on Streamlit

Point Streamlit at `streamlit_app.py`. On Streamlit Community Cloud, put the same keys as `.env.example`in the app's *Secrets* (e.g. `DATABASE_URL = "postgresql://..."`); top-level secrets are exposed as environment variables, which is what `app/core/config.py` reads. Plain `postgresql://` and `postgres://` URLs use the installed `psycopg2` driver. The database must be reachable from the internet (or via an allowed IP), so prefer a read-write user limited to this table.

## Tests

```bash
pip install -r requirements-dev.txt
pytest                                                  # logic tests; DB/API tests are skipped
TEST_DATABASE_URL=postgresql://user:pw@localhost:5432/postgres pytest   # everything
```

Database tests create a throw-away schema and drop it afterwards; your real tables are not touched.

## Notes / next steps

- `country` is free text up to 100 characters and matches the existing `website.website_info.country` column.
- To make an upload also overwrite name/type/country of known sites, change `set_` in `app/repositories/website_repository.py`.
- `create_all` does not alter existing tables. Once the schema starts changing, add Alembic.
- `normalize_link` is frozen: changing it changes every `website_id`.