# ViralNow Ingest & Feature Pipeline Specification

## Overview
This document details the ingestion and feature-extraction pipeline for ViralNow / GoViralNow. The objective is to transform raw social media assets (short-form video, audio-only, and text-based posts) into a structured feature set that powers the viral score engine and downstream analytics services. The pipeline is modular so that new modalities and models can be plugged in without breaking the existing API contract.

```
Asset Upload/Link → Ingestion Orchestrator → Modality Extractors → Feature Store → Scoring Service
```

## 1. Ingestion Layer

### 1.1 Entry Points
- **Direct Uploads**: Creators upload MP4/MOV (video) or MP3/WAV (audio) assets through the web/mobile clients. Files are streamed to object storage (e.g., S3-compatible bucket) with signed URLs.
- **External Links**: Users submit URLs to TikTok, YouTube Shorts, Instagram Reels, or X posts. A link resolver fetches metadata and downloads media assets via platform APIs or headless scraping workers subject to rate limits.
- **Text Input**: Raw captions or scripts are submitted directly through the API and stored as UTF-8 JSON payloads.

### 1.2 Orchestration
- **Ingestion Orchestrator** (FastAPI background task or Celery/RQ worker) validates payloads, normalizes filenames, and publishes jobs onto a queue (Redis Streams) keyed by asset ID.
- **Metadata Capture**: Store user ID, platform, language hints, timestamps, and source URL in PostgreSQL for traceability. All jobs carry a correlation ID for audit logging.

## 2. Modality Extractors

Each extractor subscribes to modality-specific queues and writes features into the feature store (PostgreSQL or columnar warehouse). Extractors should be containerized microservices to scale independently.

### 2.1 Audio Feature Service
- **Preprocessing**: Downmix to mono, resample to 16 kHz, normalize gain.
- **Feature Extraction**:
  - Compute spectral features with `librosa` (MFCCs, chroma, spectral centroid, roll-off, zero-crossing rate).
  - Measure integrated loudness (LUFS) via `pyloudnorm` for consistent perceived loudness comparisons.
  - Run beat tracking to derive tempo, beat strength, and rhythm stability metrics.
  - Generate a *trending-sound hash* by combining tempo, key, and timbre fingerprints to match trending audio clips.
- **Outputs**: JSON blob with per-frame stats and aggregate summary statistics (mean, variance, dynamics descriptors).

### 2.2 Voice Feature Service
- **Speech Activity Detection**: Use diarization (e.g., `pyannote.audio`) to segment speakers and estimate speaker counts.
- **Prosody Analysis**:
  - Extract pitch contours (`pyworld` or `praat-parselmouth`) and voiced/unvoiced ratios.
  - Compute speaking rate, articulation rate, and energy envelopes.
  - Derive emotion cues from pitch variance, intensity, and speaking style features.
- **Outputs**: Speaker-specific timelines, dominance ratios, prosodic feature vectors.

### 2.3 Text Feature Service
- **Transcription**: Run Whisper (medium or large-v2 depending on resource tier) to generate transcripts with timestamps.
- **Segmentation**: Apply sentence boundary detection (spaCy or `nltk` Punkt) on the transcript aligned with timestamps.
- **Emotion Classification**: Feed sentences into a transformer-based classifier (e.g., `go-emotions` fine-tuned model) to score emotions/intents.
- **Additional NLP Features**: Keyword extraction, readability scores, hook strength heuristics.
- **Outputs**: Structured transcript (segments, timestamps, speaker IDs), emotion scores per segment, aggregate sentiment trends.

### 2.4 Vision Feature Service
- **Frame Sampling**: Decode video at 2–4 fps adaptive sampling to balance cost and fidelity.
- **Face & Valence Detection**: Run a lightweight face detector (e.g., RetinaFace MobileNet) and a facial affect model to score valence/arousal per detected face.
- **Shot-Change Detection**: Compute HSV histogram differences or use `pySceneDetect` to detect cuts, returning shot boundaries and pacing metrics.
- **Motion Vectors**: Extract optical flow (Farneback or lightweight RAFT) to quantify motion intensity and directionality.
- **OCR for Captions**: Apply `easyocr` or `tesseract` on sampled frames to capture on-screen text, linking back to timestamps.
- **Outputs**: Shot timeline, face presence charts, motion statistics, extracted text overlays.

## 3. Feature Store & Schema

- **Storage Medium**: PostgreSQL for metadata + structured aggregates, object storage (Parquet files) for high-dimensional temporal features.
- **Schema Overview**:
  - `assets`: asset_id (PK), user_id, platform, source_url, upload_ts.
  - `features_audio`, `features_voice`, `features_text`, `features_vision`: asset_id (FK), version, summary JSONB, vectors stored as arrays.
  - `transcripts`: asset_id, segment_id, start_ts, end_ts, speaker_label, text, emotion_scores JSONB.
  - `shots`: asset_id, shot_id, start_ts, end_ts, motion_score, faces_present, overlay_text.
- **Versioning**: Include `model_version` and `feature_schema_version` fields for reproducibility.

## 4. Implementation Plan

1. **Bootstrap Infrastructure**
   - Extend FastAPI service with upload and link endpoints.
   - Configure object storage bucket and Redis Streams queues.
   - Define PostgreSQL schemas and migration scripts (Alembic).

2. **Build Extractor Services**
   - Containerize each modality extractor with shared base image (Python 3.10, CUDA optional).
   - Implement consistent logging, tracing, and health checks.
   - Use feature validation contracts (pydantic models) to enforce schema.

3. **Pipeline Coordination**
   - Implement orchestrator worker that triggers extractors and monitors job status.
   - Store intermediate artifacts (transcripts, OCR text) in object storage with metadata entries.

4. **Testing Strategy**
   - Unit tests per extractor for feature vector correctness using synthetic fixtures.
   - Integration tests running end-to-end on sample assets, asserting schema conformance.
   - Performance benchmarks to ensure throughput targets (≤ 5 min processing for 60s video).

5. **Deployment Considerations**
   - Use Docker Compose locally; Helm charts/Kubernetes for production.
   - Enable GPU-backed nodes for Whisper + vision inference.
   - Centralized monitoring (Prometheus + Grafana) with alerting on job failures.

6. **Security & Compliance**
   - Enforce signed URLs, JWT-authenticated API calls, and encrypted storage.
   - Redact PII from logs and enforce retention policies.

## 5. Interfaces & Contracts

- **API Contract**: `/api/v1/assets/{asset_id}/features` returns consolidated feature payload, grouped by modality, including processing status and timestamps.
- **Event Model**: Queue messages encoded as JSON: `{ "asset_id": str, "modality": "audio|voice|text|vision", "payload_uri": str, "ingested_at": timestamp }`.
- **Version Control**: Publish schema changes via migrations and bump extractor Docker tags simultaneously.

## 6. Future Extensions

- Add social listening data (hashtag popularity, trending audio metrics) to augment trending-sound hash matching.
- Introduce reinforcement feedback loop using post-publication performance to recalibrate feature weights.
- Experiment with multimodal transformers for joint embeddings feeding the viral score model.

