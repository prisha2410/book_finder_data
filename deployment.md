# Deployment Guide - Book Finder Semantic Search

This guide covers deploying the Book Finder Semantic Search API to various cloud platforms.

---

## Prerequisites

Before deploying, ensure you have:

1. ✅ Completed the ETL pipeline (database created)
2. ✅ Built the search index (embeddings generated)
3. ✅ Tested locally (API works on localhost)

---

## Deployment Options

### 🚀 Quick Comparison

| Platform | Cost | Ease | Performance | Recommended For |
|----------|------|------|-------------|-----------------|
| **Render** | Free/$7 | ⭐⭐⭐⭐⭐ | Good | Production |
| **Railway** | $5/mo | ⭐⭐⭐⭐⭐ | Good | Development |
| **Fly.io** | $0-2/mo | ⭐⭐⭐⭐ | Excellent | Production |
| **Heroku** | $7/mo | ⭐⭐⭐⭐⭐ | Good | Quick deploys |
| **Digital Ocean** | $6/mo | ⭐⭐⭐ | Excellent | Full control |

---

## Option 1: Render.com (Recommended)

**Best for:** Production deployment with minimal cost

### Step 1: Prepare Repository

```bash
# Ensure these files exist:
# - Dockerfile
# - requirements.txt
# - requirements_search.txt
# - data/books.db
# - data/embeddings.pkl
# - data/book_index.pkl

# Push to GitHub
git add .
git commit -m "Add semantic search"
git push origin main
```

### Step 2: Create Render Account

1. Go to https://render.com
2. Sign up (free, no credit card needed)
3. Connect your GitHub account

### Step 3: Create Web Service

1. Click "New +" → "Web Service"
2. Select your repository
3. Configure:
   ```
   Name: book-search-api
   Environment: Docker
   Region: Oregon (US West)
   Instance Type: Free (or Starter for better performance)
   ```

4. Add environment variables (if needed):
   ```
   PYTHONUNBUFFERED=1
   ```

5. Click "Create Web Service"

### Step 4: Wait for Build

- Initial build: 5-10 minutes
- Subsequent builds: 2-3 minutes

### Step 5: Access Your API

Your API will be available at:
```
https://book-search-api-xxxx.onrender.com
```

Test it:
```bash
curl https://your-url.onrender.com/health
```

### Render-Specific Notes

**Free Tier Limitations:**
- Spins down after 15 minutes of inactivity
- First request after spin-down: 30-60 seconds
- 512MB RAM (sufficient for our model)

**Upgrading:**
- Starter plan: $7/mo
- Always-on, no spin-down
- 512MB RAM guaranteed

---

## Option 2: Railway.app

**Best for:** Quick deployment with built-in database

### Step 1: Install Railway CLI

```bash
npm install -g @railway/cli
railway login
```

### Step 2: Initialize Project

```bash
# In your project directory
railway init
```

### Step 3: Deploy

```bash
railway up
```

That's it! Railway handles everything.

### Step 4: Get Your URL

```bash
railway domain
```

### Railway-Specific Notes

- $5 credit per month (free tier)
- ~500MB RAM usage → ~$5/mo
- Automatic HTTPS
- Built-in metrics

---

## Option 3: Fly.io

**Best for:** Edge deployment (global CDN)

### Step 1: Install Fly CLI

```bash
# macOS
brew install flyctl

# Linux
curl -L https://fly.io/install.sh | sh

# Windows
powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
```

### Step 2: Sign Up

```bash
fly auth signup
```

### Step 3: Launch App

```bash
fly launch
```

Answer the prompts:
```
? Choose an app name: book-search-api
? Choose a region: sea (Seattle)
? Would you like to set up a Postgresql database? No
? Would you like to deploy now? Yes
```

### Step 4: Access Your API

```
https://book-search-api.fly.dev
```

### Fly.io-Specific Notes

**Pricing:**
- Free: 3 shared VMs (256MB RAM each)
- Our app needs ~512MB → $1.94/mo

**Configuration:**

Edit `fly.toml`:
```toml
[env]
  PORT = "8000"

[[services]]
  internal_port = 8000
  protocol = "tcp"

  [[services.ports]]
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443
```

---

## Option 4: Heroku

**Best for:** Enterprise features

### Step 1: Install Heroku CLI

```bash
# macOS
brew tap heroku/brew && brew install heroku

# Other platforms: https://devcenter.heroku.com/articles/heroku-cli
```

### Step 2: Login

```bash
heroku login
```

### Step 3: Create Heroku App

```bash
heroku create book-search-api
```

### Step 4: Create Procfile

```bash
echo "web: uvicorn api.main_search:app --host 0.0.0.0 --port \$PORT" > Procfile
```

### Step 5: Deploy

```bash
git add Procfile
git commit -m "Add Procfile"
git push heroku main
```

### Step 6: Access

```
https://book-search-api.herokuapp.com
```

### Heroku-Specific Notes

**Pricing:**
- No free tier (as of 2022)
- Eco dyno: $5/mo
- Basic dyno: $7/mo

**Benefits:**
- Add-ons ecosystem
- Automatic SSL
- Built-in CI/CD

---

## Option 5: Docker on VPS (Digital Ocean, AWS, etc.)

**Best for:** Full control, best performance

### Step 1: Create VPS

Create a Ubuntu 22.04 droplet/instance:
- 1GB RAM minimum
- 25GB disk minimum

### Step 2: SSH into Server

```bash
ssh root@your-server-ip
```

### Step 3: Install Docker

```bash
# Update packages
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y
```

### Step 4: Clone Repository

```bash
git clone https://github.com/your-username/book_finder_data.git
cd book_finder_data
```

### Step 5: Build and Run

```bash
docker-compose up -d
```

### Step 6: Setup Nginx (Optional, for HTTPS)

```bash
# Install Nginx
apt install nginx -y

# Configure reverse proxy
cat > /etc/nginx/sites-available/book-api << 'EOF'
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
EOF

ln -s /etc/nginx/sites-available/book-api /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### Step 7: Setup SSL with Let's Encrypt

```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d your-domain.com
```

---

## Data Persistence

### Important: Include Data in Deployment

Your deployment must include:
```
data/
  ├── books.db          # SQLite database
  ├── embeddings.pkl    # Pre-computed embeddings
  └── book_index.pkl    # Book metadata index
```

### Options:

#### Option A: Include in Git (if < 100MB)

```bash
# Remove data from .gitignore
sed -i '/data\//d' .gitignore

# Add data files
git add data/books.db data/embeddings.pkl data/book_index.pkl
git commit -m "Add data files"
```

#### Option B: Use Git LFS (if > 100MB)

```bash
# Install Git LFS
git lfs install

# Track large files
git lfs track "*.pkl"
git lfs track "*.db"

# Add and commit
git add .gitattributes
git add data/
git commit -m "Add data files with LFS"
```

#### Option C: Download on Deploy

Add to your `Dockerfile`:
```dockerfile
RUN curl -o data/books.db https://your-storage/books.db
RUN curl -o data/embeddings.pkl https://your-storage/embeddings.pkl
RUN curl -o data/book_index.pkl https://your-storage/book_index.pkl
```

#### Option D: Mount External Volume (VPS only)

```yaml
# docker-compose.yml
volumes:
  - ./data:/app/data:ro  # Read-only mount
```

---

## Environment Variables

### Required Variables

```bash
# Optional: Adjust these if needed
PYTHONUNBUFFERED=1
PORT=8000
```

### Platform-Specific Setup

**Render:**
- Dashboard → Environment → Add Variables

**Railway:**
```bash
railway variables set PYTHONUNBUFFERED=1
```

**Fly.io:**
```bash
fly secrets set PYTHONUNBUFFERED=1
```

**Heroku:**
```bash
heroku config:set PYTHONUNBUFFERED=1
```

---

## Performance Optimization

### 1. Enable Gzip Compression

Add to your API:
```python
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 2. Add Caching

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

@app.on_event("startup")
async def startup():
    FastAPICache.init(InMemoryBackend())
```

### 3. Optimize Model Loading

```python
# Load model once at startup
@app.on_event("startup")
async def load_model():
    global search_engine
    search_engine = SemanticSearchEngine()
```

---

## Monitoring & Debugging

### Health Check Endpoint

```bash
curl https://your-api.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "book-finder-semantic-search",
  "indexed": true
}
```

### Check Stats

```bash
curl https://your-api.com/stats
```

### View Logs

**Render:**
- Dashboard → Logs

**Railway:**
```bash
railway logs
```

**Fly.io:**
```bash
fly logs
```

**Heroku:**
```bash
heroku logs --tail
```

---

## Troubleshooting

### Issue: Out of Memory

**Symptom:** App crashes with "Killed" or OOM error

**Solution:**
1. Upgrade to instance with more RAM (1GB minimum)
2. Use smaller model: `all-MiniLM-L6-v2` (default)
3. Reduce batch size in indexing

### Issue: Slow First Request

**Symptom:** First search takes 10+ seconds

**Solution:** This is normal - model loading time
- Add warm-up request on startup:
```python
@app.on_event("startup")
async def warmup():
    search_engine.search("test query", top_k=1)
```

### Issue: Database Not Found

**Symptom:** `sqlite3.OperationalError: no such table: books`

**Solution:** Ensure data files are included in deployment

### Issue: Embeddings Not Found

**Symptom:** "No books indexed" error

**Solution:**
```bash
# Rebuild index
curl -X POST https://your-api.com/rebuild-index
```

---

## Updating the Deployment

### Add New Books

1. Add books to CSV
2. Run ETL pipeline locally
3. Rebuild index locally
4. Commit and push:
```bash
git add data/
git commit -m "Update book database"
git push
```

5. Rebuild on server:
```bash
curl -X POST https://your-api.com/rebuild-index
```

### Update Code

```bash
git add .
git commit -m "Update search algorithm"
git push
```

Platform will auto-deploy.

---

## Cost Estimation

### Monthly Costs

| Platform | RAM | Always-On | HTTPS | Est. Cost |
|----------|-----|-----------|-------|-----------|
| Render Free | 512MB | No | Yes | $0 |
| Render Starter | 512MB | Yes | Yes | $7 |
| Railway | 512MB | Yes | Yes | $5 |
| Fly.io | 512MB | Yes | Yes | $1.94 |
| Heroku Basic | 512MB | Yes | Yes | $7 |
| DO Droplet | 1GB | Yes | Manual | $6 |

**Recommendation:**
- **Development:** Render Free
- **Production:** Fly.io or Railway

---

## Security Checklist

- [ ] Use HTTPS (all platforms provide this)
- [ ] Add rate limiting (if high traffic expected)
- [ ] Set up API keys for /rebuild-index endpoint
- [ ] Enable CORS only for specific domains
- [ ] Monitor logs for suspicious activity
- [ ] Regular backups of data files

---

## Next Steps After Deployment

1. ✅ Test the API with real queries
2. ✅ Share the URL with users/testers
3. ✅ Monitor usage and performance
4. ✅ Collect feedback
5. ✅ Iterate on the algorithm

**Your API is now live! 🎉**