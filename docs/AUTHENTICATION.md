# StoreScout account access

The landing page links to `/login`; “Try now” opens the account-creation form. Registration and sign-in use the FastAPI authentication endpoints and SQLite persistence. Passwords are salted and hashed with scrypt; only a SHA-256 hash of each random session token is stored. Sessions expire after seven days and are revoked on sign-out. Authentication attempts are limited by address and email over a fifteen-minute window. Unapproved browser origins cannot submit changes.

The frontend proxies `/api/v1` to `STORESCOUT_API_ORIGIN` (default `http://127.0.0.1:8000`). Keep `NEXT_PUBLIC_API_BASE_URL=/api/v1` for same-origin browser cookies. HTTPS deployments must set `STORESCOUT_SECURE_COOKIES=1` on the backend and configure `FRONTEND_ORIGIN` for the actual website origin.

Accounts are stored in `accounts.sqlite3` alongside the database selected by `STORESCOUT_DB_PATH`. Workspace files include a server-generated account ID in their filename. Existing unowned workspace data is preserved and is not automatically assigned to a newly registered account. Each account starts from the same labelled synthetic baseline, with private saved scenarios, evaluations and reports.

Email verification, password recovery and account administration are not implemented. No verification email or recovery action is presented in the interface. This implementation adds local account access; it does not complete the broader public-hosting acceptance criteria.

Checks cover registration, sign-in, invalid passwords, rate limiting, session cookies, expiry, sign-out revocation, origin rejection and cross-account saved-data isolation. Existing API contract fixtures now authenticate explicitly. The HTTP smoke script creates a unique test account in its isolated verification database.
