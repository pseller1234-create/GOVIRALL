# Deploy FastAPI on Render

Use this repo as a template to deploy a Python
[FastAPI](https://fastapi.tiangolo.com) service on Render.

See https://render.com/docs/deploy-fastapi or follow the steps below.

## System Design Documentation
Detailed architecture, API contracts, and rollout plans for the GOVIRALL platform live in
[`docs/system_design.md`](docs/system_design.md).

## Manual Steps

1. You may use this repository directly or
   [create your own repository from this template][fastapi-template]
   if you'd like to customize the code.
2. Create a new Web Service on Render.
3. Specify the URL to your new repository or this repository.
4. Render will automatically detect that you are deploying a Python service
   and use `pip` to download the dependencies.
5. Specify the following as the Start Command.

    ```shell
    uvicorn main:app --host 0.0.0.0 --port $PORT
    ```

6. Click Create Web Service.

## Validation Endpoint

The API now exposes `POST /api/validate` to benchmark ViralNow predictions against real performance data over a 72-hour window. Supply:

- `predicted.views`, `predicted.likes`, `predicted.comments`: time-aligned arrays representing the model's expectations.
- `predicted.platform_scores`: optional per-platform projections, e.g. `{"tiktok": [...], "youtube_shorts": [...]}`.
- `actual.public_api` and `actual.trend_benchmarks`: engagement curves sourced from public APIs and trend services.
- `actual.platform_specific`: realized outcomes for each platform model you track.

Example payload:

```json
{
  "predicted": {
    "views": [1200, 2400, 3600],
    "likes": [140, 310, 520],
    "comments": [12, 25, 41],
    "platform_scores": {"tiktok": [0.91, 0.94, 0.96], "youtube_shorts": [0.77, 0.81, 0.84]}
  },
  "actual": {
    "public_api": {"views": [1100, 2500, 3500], "likes": [130, 300, 500], "comments": [10, 23, 40]},
    "trend_benchmarks": {"views": [1000, 2200, 3100], "likes": [115, 270, 430], "comments": [9, 21, 33]},
    "platform_specific": {"tiktok": [0.89, 0.93, 0.95], "youtube_shorts": [0.74, 0.80, 0.82]}
  },
  "window_hours": 72
}
```

The service returns Pearson correlations per source plus an overall score. A run is considered successful when the aggregate correlation meets or exceeds the default `0.85` threshold.

Or simply click:

[![Deploy to Render][render-badge]][render-deploy]

## GOVIRALL Product Context

You have an existing Viral Score App that estimates how “viral” a post or asset might become
based on early engagement. For this iteration, the goal is to build on the current product to
improve prediction accuracy, expand data sources, and expose scores via an API/UI for
creators and growth teams.

### App Name (Working Title)
- **ViralNow / GoViralNow**

### Tagline
- “Predict. Optimize. Go Viral.”

### App Overview

ViralNow is an AI-powered web and mobile application that analyzes short-form videos, posts,
 or links (TikTok, YouTube Shorts, Instagram Reels, X, etc.) to generate a 0–100 “Viral Score” — a
 scientific measure of how likely a piece of content is to go viral.

The app helps creators, brands, and agencies understand what makes content blow up — and provides
specific, data-backed suggestions to improve performance before posting.

Users can upload a video, paste a link, or input text. The system then runs AI analysis (using NLP +
CV models) and returns a full viral intelligence report in seconds.

### Core Features
- **Upload or Link Input**
  - Accepts video, post URL, or raw text (caption/script).
  - Auto-detects platform (TikTok, YouTube, Instagram, X).
- **AI Viral Score Engine**
  - Calculates a 0–100 score + confidence %.
  - Shows how it performs across each platform.
  - Uses visual, audio, and text analysis (hook strength, pacing, emotion, clarity,
    engagement cues).
- **Why It Works / Why It Won’t**
  - Bullet summary explaining strengths and weaknesses.
  - “Missing Elements” section (e.g., “No emotional hook,” “Weak retention curve,”
    “Text overlay too late”).
- **Optimization Suggestions**
  - Auto-generate 5 improved hook lines.
  - Suggest best posting times, hashtags, and sound types.
  - Recommend captions, pacing tweaks, or thumbnail ideas.
- **Competitive Context**
  - Compare to trending posts in the same niche.
  - Provide actionable feedback (e.g., “+captions +faster cuts +high contrast”).
- **Creator Dashboard**
  - View history of uploads and progress over time.
  - Track average viral score, niche success rate, and engagement trendlines.
- **Pro Tier / Academy (Future)**
  - Access “Viral Blueprint” lessons and case studies.
  - Sandbox “Prediction Lab” for testing content drafts before posting.
  - Community leaderboard and gamified growth challenges.

### Tech Stack (Planned)
- **Backend**: FastAPI (Python), Redis (rate limits + queues), PostgreSQL (analytics)
- **Frontend**: React + Tailwind (Web), React Native (Mobile)
- **AI Models**: OpenAI (text), CLIP / Whisper / Vision Transformers (video + audio)
- **Deployment**: Docker + Render / Fly.io
- **Security**: JWT Auth, Argon2 Hashing, API key system
- **Integrations**: YouTube Data API, TikTok Insights, Google Trends

### Target Users
- Content creators — YouTubers, TikTokers, influencers
- Marketing teams / agencies — running campaigns and audits
- Educators / coaches — teaching viral content strategy

### Why It’s Unique
Unlike typical analytics tools, ViralNow focuses on pre-launch prediction and creative feedback, not
just post-performance stats. It gives creators the power to simulate the algorithm — before
publishing.

### Vision
To become the global standard for viral content prediction — the “credit score” for social media
success.

[fastapi-template]: https://github.com/render-examples/fastapi/generate
[render-badge]: https://render.com/images/deploy-to-render-button.svg
[render-deploy]: https://render.com/deploy?repo=https://github.com/render-examples/fastapi
