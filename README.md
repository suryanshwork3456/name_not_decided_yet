# For Local Build

## 1. Navigate to server directory
cd server

## 2. Create virtual environment
python -m venv venv

## 3. Activate virtual environment

**On Windows:**
.\venv\Scripts\activate
**On Mac/Linux/Git Bash:**
source venv/bin/activate

## 4. Install dependencies
pip install -r requirements.txt

## 5. Set up environment variables

**On Windows:**
Copy-Item .env.example .env
**On Mac/Linux/Git Bash:**
cp .env.example .env

Now open the `.env` file in any code editor and fill in your own values:
- `DATABASE_URL` — your local PostgreSQL connection string (`postgresql://postgres:your_password@localhost:5432/sih_gis_db`)
- `SECRET_KEY` — any random string (generate one with `python -c "import secrets; print(secrets.token_hex(32))"`)

## 6. Run local development server
uvicorn app.main:app --reload


# 🔐 Authentication Architecture

This project uses **OAuth2 with JWT (JSON Web Tokens)** for stateless authentication and **Argon2id** for password hashing. The interaction between Next.js, FastAPI, and PostgreSQL is completely decoupled and stateless.

---

## 🛠️ Security & Tech Stack Rationale

| Tool / Standard | Alternative | Why We Chose It |
| --- | --- | --- |
| **OAuth2 + JWT** | Session Cookies / Basic Auth | **Stateless & Scalable:** Enables verification of identity via cryptographic signatures ($HS256$) without querying Redis or PostgreSQL on every request. |
| **Argon2id** | Bcrypt / SHA-256 / MD5 | **Memory-Hard Hashing:** Winner of the Password Hashing Competition. It forces physical RAM allocation during computation, preventing GPU/ASIC brute-force attacks. |
| **PyJWT** | `python-jose` | **Modern & Lightweight:** Actively maintained Python implementation for encoding and decoding JWTs cleanly without deprecated dependencies. |

---

## 🔄 Complete Authentication Flow

```
                                +-------------------+
                                | Next.js Frontend  |
                                +-------------------+
                                  /       |       \
               1. POST /register /        |        \ 8. GET /fields
               {email, password}/         |         \ Header: Bearer <JWT>
                               /          |          \
                              /   5. POST | /login    \
                             v            v            v
                     +---------------------------------------+
                     |            FastAPI Backend            |
                     +---------------------------------------+
                       |                  |                 |
      2. Hash Argon2   |                  | 6. Verify Hash  | 9. Decode JWT
                       v                  v                 v
            +---------------------+   +-------+   +-------------------+
            | PostgreSQL Database |   | PyJWT |   | get_current_user  |
            +---------------------+   +-------+   +-------------------+

```

---

## 🗂️ Detailed Pipeline Phases

### Phase 1: User Registration (`POST /auth/register`)

1. **Request:** Next.js sends `POST /auth/register` with JSON body `{ "email": "farmer@field.com", "password": "SecretPassword123" }`.
2. **Validation:** FastAPI validates input structure using the `UserCreate` Pydantic model.
3. **Hashing:** `pwd_context.hash(user_in.password)` from `passlib.context.CryptContext(schemes=["argon2"])` computes a memory-hard hash.
4. **Storage:** SQLAlchemy / SQLModel inserts the user record into PostgreSQL storing the Argon2 hash string.

### Phase 2: User Login & Token Generation (`POST /auth/login`)

1. **Request:** Next.js submits form data (`application/x-www-form-urlencoded`) containing `username` and `password`.
2. **Parsing:** FastAPI's `OAuth2PasswordRequestForm = Depends()` parses request credentials.
3. **Verification:** `pwd_context.verify(form_data.password, db_user.hashed_password)` validates the incoming password against the stored Argon2 hash.
4. **Encoding:** `jwt.encode(payload, SECRET_KEY, algorithm="HS256")` constructs the JWT containing `sub` (User ID) and `exp` (expiration timestamp).
5. **Response:** FastAPI returns `{ "access_token": "eyJhbG...", "token_type": "bearer" }`.

### Phase 3: Accessing Protected Endpoints (`GET /fields`)

1. **Request:** Next.js attaches token to header: `Authorization: Bearer <token>`.
2. **Extraction:** `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")` intercepts and pulls the token string.
3. **Validation & Context Injection:** `get_current_user` dependency executes `jwt.decode(token, SECRET_KEY, algorithms=["HS256"])`, checks expiration, fetches the `User` object from PostgreSQL, and injects it directly into route parameters:
```python
@app.get("/fields")
def get_user_fields(current_user: User = Depends(get_current_user)):
    return db.query(Field).filter(Field.owner_id == current_user.id).all()

```



---

## 📊 Summary Mapping Table

| Stage | Action | FastAPI Dependency / Library Function | Purpose |
| --- | --- | --- | --- |
| **Register** | Hash Password | `passlib.context.CryptContext.hash()` | Encrypts raw password into Argon2 hash before DB insertion. |
| **Login** | Parse Form Data | `OAuth2PasswordRequestForm = Depends()` | Extracts `username` and `password` from request payload. |
| **Login** | Verify Password | `passlib.context.CryptContext.verify()` | Validates incoming string against stored Argon2 hash. |
| **Login** | Issue Token | `jwt.encode()` (`pyjwt`) | Generates signed JWT payload (`sub`, `exp`). |
| **Protected Route** | Extract Bearer Token | `OAuth2PasswordBearer(tokenUrl=...)` | Extracts token string from `Authorization` HTTP header. |
| **Protected Route** | Decode Token | `jwt.decode()` (`pyjwt`) | Verifies cryptographic signature and expiration timestamp. |
| **Protected Route** | Inject User Context | `get_current_user()` (`Depends()`) | Resolves user record and exposes it to API route handlers. |