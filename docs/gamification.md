# Ethical Engagement Blueprint

This blueprint operationalizes the "reinforce daily usage without manipulation" principle. Every mechanic is measured against a
user’s craft progression (Engagement Factor uplift, quicker rise times, consistent quality) rather than grind or sunk-cost
pressure.

## Guardrails (Non-Negotiable)

| Guardrail | Implementation Notes |
| --- | --- |
| **Transparency** | Surface the Engagement Factor (EF) inputs in-product: `EF = (Hook × Retention × Interaction Quality) ÷ Normalized Baseline`. Each feedback tile links to the contributing metric deltas. |
| **Time-boxing** | Hard-cap daily missions at 3 focused drills. Display remaining drills, show reset time, and block additional quests with "Come back tomorrow" messaging. |
| **No dark patterns** | Ban artificial scarcity timers, expiring boosts, or fear-driven copy. UI copy reviews must include a "manipulation check". |
| **Opt-outs & controls** | Streaks, leaderboards, and social share prompts default to opt-in, with an always-visible toggle in Settings → Motivation. Preferences sync across devices. |

## Core Positive Mechanics

### Craft XP (Progress-Oriented)
- XP is awarded only when EF or Rise-Time improves versus the creator’s personal baseline.
- Store baseline metrics per asset type to avoid regressions when experimenting in new formats.
- XP breakdown UI: `+12 XP • EF +4 • Rise-Time -0.6 s` for immediate clarity.

### Daily Micro-Quests (Focused Deliberate Practice)
- Generate 2–3 quests per day, each targeting a single skill (hook sharpness, pacing, caption clarity).
- Quests include a measurement target (e.g., "Lift Hook Strength to ≥78 within 2 attempts").
- Upon completion, run an immediate rescore pipeline and show before/after metrics.

### Before/After Gallery (Visual Reinforcement)
- Capture key frames, captions, and waveform snippets pre- and post-edit.
- Highlight the delta with annotations ("Cut intro dead air from 2.1 s → 0.8 s").
- Allow export for coaching portfolios while automatically redacting any audience PII.

### Coaching Streaks (Learning Momentum)
- Increment streaks only when a drill is attempted and feedback is reviewed.
- Streak loss is never penalizing; instead, surface "Pause logged" with a prompt to resume when ready.
- Users can disable streak tracking entirely without losing historical performance data.

### Creator Baseline Cards (Self-Referential Wins)
- For every asset type, maintain a "personal best" snapshot (EF, Rise-Time, Completion Rate).
- Celebrate new highs with context ("New EF Personal Best: 82 (+7 vs 30-day avg)").
- Include a "See what changed" button linking to the relevant before/after gallery and micro-quest logs.

## Feedback & Analytics Loop
- **Session Recap Modal:** End each session with a recap that lists quests attempted, XP earned, and EF trendlines with raw numbers.
- **Transparency Drawer:** A persistent drawer documents how EF was calculated, which sensors contributed, and the timestamp of the last model update.
- **Opt-out Confirmation:** When users disable a mechanic, capture anonymous telemetry (reason codes) to refine defaults without re-enabling automatically.

## Implementation Checklist
- [ ] Document EF formula and metric definitions in public FAQs and in-app tooltips.
- [ ] Build quest generator templates with explicit time-boxing and measurable success criteria.
- [ ] Add toggles for streaks, leaderboards, and notifications in Settings; ensure server persists preferences.
- [ ] Instrument XP awards to require positive delta versus baseline; log calculations for audit.
- [ ] Produce redaction guidelines for before/after galleries and enforce via automated checks.
- [ ] Schedule quarterly copy audits focused on avoiding fear-based or scarcity-driven language.

Adhering to these guidelines ensures the engagement surface accelerates creative mastery, remains transparent, and respects user
agency at every touchpoint.
