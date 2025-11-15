# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based RAG (Retrieval-Augmented Generation) chatbot system for Orange Burkina Faso. It combines web scraping, vector search, and local LLM inference to provide intelligent responses about Orange services and local knowledge (national anthem, greetings in local languages, etc.).

## Architecture

The system consists of three main components:

### 1. Data Collection (Scrapy-based web scraper)
- **Spider**: `orange_scraper/spiders/orange_services_spider.py` - Crawls orange.bf website
- **Configuration**: `orange_scraper/settings.py` and `scrapy.cfg`
- Extracts service information from predefined URL patterns (assistance, catalogue, services-mobile)
- Outputs raw data to `orange_services.json`

### 2. Data Processing Pipeline
Located in `data_processing/` directory:
- **clean_orange.py**: Cleans HTML entities and tags from scraped data → `orange_services_clean.json`
- **create_embeddings.py**: Generates sentence embeddings using `sentence-transformers/all-MiniLM-L6-v2` and creates FAISS index → `orange_faq.index` + `metadata.json`
- **elasticsearch_manager.py**: ElasticsearchManager class for bulk indexing
- **index_data.py**: Indexes cleaned data into Elasticsearch (uses hardcoded credentials - see security note below)
- **local_knowledge.py**: Hardcoded local facts (national anthem in 3 languages, greetings in Mooré/Dioula, president name)

### 3. RAG Server
- **rag_server_gpt4all.py**: FastAPI server with `/ask` endpoint
  - Uses FAISS for semantic search (retrieves top 5 passages)
  - Generates responses with GPT4All model (`orca-mini-3b-gguf2-q4_0.gguf`)
  - Model file must be in project root directory
- **search_faq.py**: CLI tool for testing FAISS search and local knowledge retrieval

## Common Commands

### Scraping
```bash
# Run the spider from project root
scrapy crawl orange_services

# Output: orange_services.json and PDFs in ./pdfs/
```

### Data Processing
```bash
# Clean scraped data
python data_processing/clean_orange.py

# Generate embeddings and FAISS index
python data_processing/create_embeddings.py

# Index to Elasticsearch
python data_processing/index_data.py
```

### RAG Server
```bash
# Start FastAPI server (requires orca-mini-3b-gguf2-q4_0.gguf in root)
uvicorn data_processing.rag_server_gpt4all:app --reload

# Test search CLI
python data_processing/search_faq.py
python data_processing/search_faq.py "comment activer orange money"
```

### Environment Setup
```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies (no requirements.txt - install manually)
pip install scrapy beautifulsoup4 lxml fastapi uvicorn pydantic faiss-cpu sentence-transformers gpt4all elasticsearch tqdm numpy
```

## Key Technical Details

### Dependencies
- **Python 3.11** (based on venv structure)
- **Scrapy** + **BeautifulSoup4**: Web scraping and HTML parsing
- **FAISS**: Vector similarity search (CPU version)
- **sentence-transformers**: Embedding generation (all-MiniLM-L6-v2 model)
- **GPT4All**: Local LLM inference (Orca-Mini 3B quantized)
- **FastAPI**: REST API server
- **Elasticsearch**: Optional search backend (uses cloud instance)

### File Flow
```
orange.bf → [Scrapy] → orange_services.json
            ↓
         [clean_orange.py] → orange_services_clean.json
            ↓
         [create_embeddings.py] → orange_faq.index + metadata.json
            ↓
         [rag_server_gpt4all.py] ← User queries via /ask endpoint
```

### Large Model Files
- `ggml-gpt4all-j-v1.3-groovy.bin` (3.5 GB) - Older GPT4All model
- `orca-mini-3b-gguf2-q4_0.gguf` (1.8 GB) - Currently used model
- These files are required in the project root for LLM inference

## Security Considerations

**CRITICAL**: `data_processing/index_data.py:47-48` contains hardcoded Elasticsearch credentials:
- Host: `9ce0d46a529144858720414e2ba0586e.us-central1.gcp.cloud.es.io:443`
- API Key: `ZVg2cWVab0JVQVQ3TTVEVjI4bTQ6cl9IczgtYkNaQmRDMG1rMzgycm5hUQ==`

These should be moved to environment variables or a config file before committing changes or sharing code.

## Development Notes

- The project is NOT a git repository
- Spider uses custom User-Agent: `HumanoidAssistantBot` to identify itself
- Respects `robots.txt` with 1-second download delay and autothrottle
- FAISS index uses Inner Product (IP) similarity after L2 normalization (equivalent to cosine similarity)
- RAG context retrieval: top 5 passages by default
- Local knowledge queries bypass FAISS search (president, anthem, greetings)

## Extending the System

### To scrape additional sections:
1. Add URLs to `start_urls` in `orange_services_spider.py:10-15`
2. Update link-following logic in `parse()` method at line 53-57
3. Re-run full pipeline: scrape → clean → embed → index

### To modify RAG behavior:
- Change `TOP_K` in `rag_server_gpt4all.py:19` to retrieve more/fewer passages
- Adjust prompt template in `generate_response()` at line 53
- Switch embedding model by changing `EMBEDDING_MODEL` constant

### To add more local knowledge:
- Edit `local_facts` dictionary in `local_knowledge.py:3-112`
- Update `get_fact()` function with new query patterns
