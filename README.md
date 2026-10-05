# MeetIQ 🎙️

### AI Meeting Intelligence Platform

MeetIQ is an AI-powered meeting intelligence platform that converts meeting recordings into structured, actionable insights.

Instead of manually reviewing an entire meeting, MeetIQ processes the recording and generates a concise meeting summary, key topics, decisions, action items, and unresolved issues.

---

## 🚀 Features

- 🎙️ Upload meeting recordings
- 📝 Automatic speech-to-text transcription
- 🤖 AI-generated meeting summaries
- 🔑 Key topic extraction
- ✅ Decision extraction
- 📌 Action item identification
- ⚠️ Unresolved issue detection
- 📊 Interactive meeting intelligence dashboard
- 🔌 FastAPI backend
- ⚛️ React + Vite frontend
- 🧠 Local LLM-based meeting analysis
- 📄 Structured JSON meeting analysis

---

## 🏗️ Architecture

```text
                    ┌──────────────────────┐
                    │      User            │
                    │ Upload / Record      │
                    │      Meeting         │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   React Frontend     │
                    │   React + Vite       │
                    └──────────┬───────────┘
                               │
                               │ HTTP API
                               ▼
                    ┌──────────────────────┐
                    │   FastAPI Backend    │
                    │      Python          │
                    └──────────┬───────────┘
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
          ┌─────────────────┐    ┌─────────────────┐
          │ Speech-to-Text  │    │ Meeting Analyzer│
          │ Transcription   │    │ Local LLM       │
          └────────┬────────┘    └────────┬────────┘
                   │                      │
                   └──────────┬───────────┘
                              ▼
                    ┌──────────────────────┐
                    │ Structured Meeting   │
                    │ Intelligence          │
                    │                      │
                    │ • Summary             │
                    │ • Key Topics          │
                    │ • Decisions           │
                    │ • Action Items        │
                    │ • Unresolved Issues   │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Meeting Intelligence │
                    │ Dashboard            │
                    └──────────────────────┘
