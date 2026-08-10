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


# 🛰️ Feature 1 Architecture: Field-Level Satellite Monitoring & Health Analytics

This feature provides automated macro-level monitoring by combining satellite imagery, spatial raster calculations, real-time meteorological conditions, and machine learning to evaluate field-wide crop health and detect localized vegetation stress.

---

## 🛠️ Security & Tech Stack Rationale

| Layer / Technology | Alternative | Rationale & Trade-offs |
| --- | --- | --- |
| **Next.js + Leaflet.js** | Google Maps API / Mapbox GL | **Lightweight & Open Source:** Leaflet provides native GeoJSON drawn-polygon extraction without per-map-load API costs. Integrates seamlessly with Next.js client component state. |
| **PostgreSQL + PostGIS** | MongoDB GeoJSON / MySQL Spatial | **True OGC Spatial Indexing:** Provides native spatial operators (e.g., `ST_Contains`, `ST_Intersects`, `ST_Area`) with `GIST` indexes, ensuring ultra-fast coordinate bounding box filtering. |
| **Sentinel-2 L2A Data API** | Landsat 8 / Planet Labs API | **Free High-Resolution Optical Imagery:** Offers $10\text{m}$ spatial resolution on Band 4 (Red) and Band 8 (Near-Infrared) with a 5-day revisit cycle. L2A provides Bottom-Of-Atmosphere (BOA) surface reflectance directly. |
| **Rasterio + NumPy** | GDAL CLI Scripting / QGIS Server | **In-Memory Array Processing:** `Rasterio` wraps GDAL in idiomatic Python, allowing multi-spectral band rasters to be read directly into NumPy arrays for parallelized matrix operations. |
| **Scikit-learn (Random Forest)** | XGBoost / PyTorch MLP | **Interpretable Ensemble Model:** Handles mixed feature types (NDVI array statistics, temperature, relative humidity, soil pH) with high robustness against small training set overfitting. |

---

## 🔄 End-to-End Execution Pipeline

```
[ Frontend: Next.js + Leaflet ]
            │  1. Draw field boundary & send Polygon GeoJSON
            ▼
[ FastAPI Endpoint: POST /api/v1/fields/analyze ]
            │  2. Store PostGIS Geometry & extract Bounding Box (BBOX)
            ▼
┌────────────────────────────────────────────────────────┐
│               Data Ingestion Pipeline                  │
│  ├─ Sentinel-2 API: Fetch Band 4 (Red) & Band 8 (NIR) │
│  ├─ OpenWeather API: Fetch Temp, Humidity, Rain        │
│  └─ Soil Metrics DB: Pull Soil pH & Moisture           │
└───────────────────────────┬────────────────────────────┘
                            │  3. Multi-spectral Rasters + Environmental Params
                            ▼
┌────────────────────────────────────────────────────────┐
│            Raster Processing Engine (Rasterio)         │
│  ├─ Compute Pixel Matrix: NDVI = (B8 - B4) / (B8 + B4) │
│  ├─ Mask & Clip Raster to Exact Field Polygon          │
│  └─ Extract Zonal Stats: Mean NDVI, StdDev, Bad Zones │
└───────────────────────────┬────────────────────────────┘
                            │  4. Feature Vector (NDVI Stats + Weather + Soil)
                            ▼
┌────────────────────────────────────────────────────────┐
│                Scikit-learn ML Engine                  │
│  ├─ Random Forest Classification (Health Score 0-100)  │
│  └─ Risk Flagging (Water Stress / Disease / Healthy)   │
└───────────────────────────┬────────────────────────────┘
                            │  5. Formatted JSON Payload
                            ▼
[ Next.js Dashboard: Render Color-Coded NDVI Map + Health Metrics ]

```

---

## 🗂️ Detailed Implementation Steps

### Phase 1: Boundary Submission & PostGIS Ingestion

1. **Frontend Capture:** The farmer draws a polygon over their field in Leaflet (`L.FeatureGroup` + `L.Control.Draw`). The frontend extracts coordinates in `EPSG:4326` (WGS 84 projection) standard GeoJSON format:
```json
{
  "type": "Polygon",
  "coordinates": [[[77.102, 28.704], [77.105, 28.704], [77.105, 28.708], [77.102, 28.708], [77.102, 28.704]]]
}

```


2. **Backend Insertion:** FastAPI validates input via a Pydantic GeoJSON schema and saves it using GeoAlchemy2:
```python
from geoalchemy2 import Geometry
from sqlmodel import Field, SQLModel

class FieldModel(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    geometry: str = Field(sa_column=Column(Geometry("POLYGON", srid=4326)))

```



### Phase 2: Satellite Tile Retrieval & Environmental Ingestion

1. **Bounding Box Calculation:** PostGIS computes the envelope (`ST_Envelope`) to obtain bounding coordinates $[X_{\min}, Y_{\min}, X_{\max}, Y_{\max}]$.
2. **Sentinel-2 Data Fetch:** The backend triggers an asynchronous request to Sentinel Hub / Copernicus Data Space API, requesting two specific 10m-resolution optical bands for the field's BBOX:
* **Band 4 (Red Spectrum):** $\lambda \approx 665\text{ nm}$ (absorbed by active chlorophyll)
* **Band 8 (Near-Infrared Spectrum):** $\lambda \approx 842\text{ nm}$ (reflected by leaf cellular structure)


3. **Parallel API Ingestion:** Simultaneously, the backend issues a request to OpenWeather API using the centroid (`ST_Centroid`) of the polygon to retrieve current surface temperature, humidity, and 7-day precipitation totals.

### Phase 3: Spatial Raster Operations & NDVI Processing

Using **Rasterio** and **NumPy**, the downloadedGeoTIFF raster tiles are read directly as float arrays to execute array-level calculations:

1. **NDVI Calculation:**

$$\text{NDVI} = \frac{\text{Band 8 (NIR)} - \text{Band 4 (RED)}}{\text{Band 8 (NIR)} + \text{Band 4 (RED)}}$$


* Output array contains values ranging from $-1.0$ to $+1.0$.


2. **Clipping & Masking:** `rasterio.mask.mask()` crops the square raster down to the precise boundary polygon of the field. Non-field pixels are set to `NaN` or masked out.
3. **Zonal Statistical Extraction:**
* **Mean NDVI ($\mu$):** Measures total photosynthetic capacity.
* **Standard Deviation ($\sigma$):** Identifies variation across the field.
* **Low-NDVI Zone Segmentation:** Pixels with $\text{NDVI} < 0.35$ are vectorized back into sub-polygons representing stressed zones.



### Phase 4: Machine Learning Health Assessment

The system passes extracted spatial statistics alongside weather and soil inputs into a pre-trained **Random Forest Regressor & Classifier**:

* **Feature Vector Inputs:**

$$\mathbf{x} = \begin{bmatrix} \text{Mean NDVI}, & \text{NDVI Variance}, & \text{Temp } (^\circ\text{C}), & \text{Humidity } (\%), & \text{Soil Moisture } (\%), & \text{Soil pH} \end{bmatrix}$$


* **Model Inference:**
1. Predicts **Overall Health Score** ($0 - 100$).
2. Classifies primary stress category (`Healthy`, `Water Stress`, `Nitrogen Deficiency Risk`, `Pest/Disease Stress`).



### Phase 5: Recommendation Engine & Dashboard Output

A lightweight rule engine constructs targeted action items based on model classifications:

* *Condition:* If `Stress Class == Water Stress` AND `Soil Moisture < 20%`:
* *Alert:* `"Water Stress Detected in Northwest Sector."`
* *Action:* `"Initiate drip irrigation cycle within 24 hours."`



---

## 📊 Summary Mapping Table

| Pipeline Stage | Python / API Library | Primary Function | Input | Output |
| --- | --- | --- | --- | --- |
| **Polygon Ingest** | GeoAlchemy2 / PostGIS | Geospatial boundary storage | GeoJSON Polygon | Stored Geometry (`SRID 4326`) |
| **Tile Ingestion** | `httpx` / Sentinel Hub API | Fetch optical bands | Bounding Box ($X, Y$) | Band 4 (Red) & Band 8 (NIR) GeoTIFFs |
| **Raster Processing** | `rasterio`, `numpy` | Spatial matrix algebra | Multi-spectral GeoTIFFs | Masked NDVI Matrix & Zonal Stats |
| **Weather Ingest** | OpenWeather API | Meteorological data pull | Lat/Lon Centroid | Temp, Humidity, Rain (JSON) |
| **Health Prediction** | `scikit-learn` (Random Forest) | Stress & risk scoring | Feature vector ($\mathbf{x}$) | Health Score ($0-100$) + Stress Flag |