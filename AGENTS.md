# Repository Guidelines

## Project Structure & Module Organization
`data_processing/` contains the FastAPI stacks (`rag_server_*.py`), cleaners, and embedding builders that output the FAISS assets (`orange_faq*.index`, `metadata*.json`) stored at root. `orange_scraper/` hosts the Scrapy spider, `static/` holds UI probes plus cached audio, `piper_bin/` and `piper_models/` keep offline voices, and helper scripts (`create_audio_index.py`, `generate_qr.py`, `test_voice_api.py`, `test_tts.py`) with WAV/MP3 fixtures stay at the root for quick QA.

## Build, Test, and Development Commands
- `python3.11 -m venv venv && source venv/bin/activate && pip install fastapi[all] scrapy sentence-transformers groq edge-tts python-dotenv` — provision dependencies.
- `uvicorn data_processing.rag_server_gpt4all:app --reload --host 0.0.0.0 --port 8000` — launch the baseline Groq + Edge-TTS API; swap modules for other stacks.
- `cd orange_scraper && scrapy crawl orange_services -O ../orange_services.json` — refresh the Orange Burkina Faso corpus before cleaning.
- `python data_processing/clean_orange_v2.py && python data_processing/create_embeddings_v2.py --index orange_faq_v2.index --metadata metadata_v2.json` — rebuild cleaned JSON and FAISS.
- `python test_voice_api.py --url http://localhost:8000 --voice-chat test_voice.wav` — verify the STT → RAG → TTS path (`--ask` covers text-only flows).
- `python test_tts.py --voice fr-FR-HenriNeural --text "Bonjour Orange Faso"` — smoke-test standalone TTS and cache refreshes.

## Coding Style & Naming Conventions
Target Python 3.11 and PEP 8 (4-space indents, `snake_case`; PascalCase for classes such as `OrangeServicesSpider`). Keep configuration constants near the top of each `rag_server_*.py`, load secrets only via `.env` + `load_dotenv()`, and document shared helpers with short docstrings and type hints.

## Testing Guidelines
No pytest suite exists; rely on the CLI probes. Update `test_voice_api.py`, rerun it plus `test_tts.py` after scraper/cleaner edits, and attach command output or JSON diffs (including `scrapy crawl ... --loglevel INFO`) to PRs for reproducibility.

## Commit & Pull Request Guidelines
Historic drops use imperative, component-prefixed subjects (`voice: optimize Piper cache`, `data: rebuild FAISS v2`); keep ≤72 characters and note environment or dependency impacts. Do not commit `.env`, sensitive FAISS dumps, or GGUF models—reference the paths in `CHEMINS_ABSOLUS.txt`. PRs should list executed commands, add UX/audio evidence, and tag RAG + audio reviewers for `rag_server_voice.py` edits.

## Security & Configuration Tips
Clone `.env.example`, store Groq/OpenAI/Edge-TTS/Piper keys there, and ensure each FastAPI module calls `load_dotenv()` before creating API clients. Put new MP3 assets in `static/audio`, refresh `audio_index.json` with `python create_audio_index.py`, scrub logs before sharing, and avoid attaching PDFs or GGUF artifacts unless essential.
