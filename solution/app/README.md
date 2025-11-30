# 🎬 CymbalFlix Discover

AI-powered movie discovery application built on AlloyDB, demonstrating:
- **Semantic Search**: Vector similarity using ScaNN index and Gemini embeddings
- **Real-Time Analytics**: Aggregations powered by the columnar engine
- **Full PostgreSQL Compatibility**: Standard Python connector and SQL patterns
- **IAM Authentication**: Secure, passwordless database access

## Quick Start (Cloud Shell)

### 1. Prerequisites

Make sure you've completed the earlier lab tasks:
- AlloyDB cluster is running (`cymbalflix-cluster`)
- Database and tables are created (from the Colab notebook)
- Your IAM user has database access

### 2. Set Up Environment

```bash
# Navigate to the app directory
cd ~cymbalflix-alloydb/solution/app

# Create your .env file from the template
cp .env.example .env

# Edit with your values
edit .env
```

Update these values in `.env`:
- `PROJECT_ID`: Your Google Cloud project ID
- `REGION`: Your Google Cloud region (e.g., `us-central1`)
- `DB_USER`: Your IAM email (e.g., `student-xxx@qwiklabs.net`)

### 3. Create Virtual Environment and Install Dependencies

```bash
# Create a virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Note:** You'll need to activate the venv (`source venv/bin/activate`) each time you open a new Cloud Shell terminal.

### 4. Run the App

```bash
streamlit run Home.py --server.port 8501
```

### 5. Access the App

Click the http://localhost:8501 link that Streamlit generates.



## App Structure

```
cymbalflix-alloydb/solution/app
├── Home.py                    # Welcome page with stats
├── pages/
│   ├── 1_Discover.py         # Semantic search (vector similarity)
│   ├── 2_Browse.py           # Filter by genre/year/rating
│   ├── 3_Search.py           # Keyword search
│   ├── 4_Analytics.py        # Columnar engine dashboards
│   └── 5_Movie.py            # Movie details + rating
├── utils/
│   ├── database.py           # AlloyDB connection handling
│   └── queries.py            # SQL queries and data access
├── requirements.txt
├── Dockerfile                # For Cloud Run deployment
└── .env.example              # Environment template
```

## Features by Page

| Page | Feature | AlloyDB Capability |
|------|---------|-------------------|
| **Discover** | Natural language search | Vector embeddings, ScaNN index |
| **Browse** | Filter & pagination | Relational queries, JOINs |
| **Search** | Keyword matching | PostgreSQL ILIKE |
| **Analytics** | Charts & dashboards | Columnar engine, aggregations |
| **Movie** | Add ratings | Transactional writes |

## Cloud Run Deployment

```bash
# Build and deploy
gcloud run deploy cymbalflix-app \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars PROJECT_ID=$PROJECT_ID,DB_USER=$DB_USER

# Get the URL
gcloud run services describe cymbalflix-app --region us-central1 --format='value(status.url)'
```

## Troubleshooting

### "Database not configured"
- Check that `.env` file exists and has correct values
- Verify `PROJECT_ID`, `REGION`, and `DB_USER` are set

### Connection errors
- Ensure AlloyDB cluster is running
- Verify your IAM user has `roles/alloydb.databaseUser`
- Check that the database `cymbalflix` exists

### "No movies found"
- Run the Colab notebook to load data if you haven't already
- Check that the `movies` table has data

## Learn More

This app is part of the **"AlloyDB: PostgreSQL Evolved"** hands-on lab.
See the lab instructions for detailed explanations of each feature.
