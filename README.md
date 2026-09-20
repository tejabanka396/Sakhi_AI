# 🌸 Sakhi AI — Voice-First Telugu AI Companion



Sakhi AI (**సఖి**) is a production-quality, voice-first AI companion built for natural, emotional, and context-aware conversations in **Telugu**, **Tanglish (Telugu in English script)**, and **English**. It combines expressive 2D character animations driven by live audio frequencies, intelligent long-term memory extraction, robust MySQL persistence, and Google Gemini generative intelligence.

---

## 🌟 Key Highlights

- 🎙️ **Voice-First Interaction Loop**: Tap, speak naturally in Telugu/Tanglish, transcribes via browser STT with Gemini audio fallback, thinks, synthesizes authentic Telugu speech, and animates the character.
- ⚡ **Instant Interruption**: Tap the microphone while Sakhi is speaking to instantly halt audio playback and avatar speaking animation, immediately entering listening mode.
- 🎨 **Living 2D Avatar**: Smooth SVG/CSS animated character with breathing, eye blinking, listening audio halos, thinking states, and mouth lip-sync driven by the Web Audio API Analyser.
- 🧠 **Contextual Long-Term Memory**: Automatically extracts personal goals, study topics, and preferences while strictly omitting passwords, OTPs, and temporary small talk.
- 🎓 **Adaptive Conversational Persona**:
  - *Casual*: Short, natural, friendly, non-robotic responses.
  - *Academic / Study*: Adapts to requests like `"7 marks answer laga explain cheyyi"` with definitions, conditions, examples, and structured summaries.
  - *Technical*: Practical code snippets and architectural guidance in Telugu or English.
- 🛡️ **Enterprise Security & Strict User Isolation**: Passwords hashed with bcrypt, access/refresh token rotation with server-side revocation on logout, hashed phone OTPs, and strict ownership checks on every database query.
- 🗄️ **MySQL 8.0 (`utf8mb4`)**: Full unicode support for Telugu script (`te-IN`), emojis, and mixed text.

---

## 🏛️ Architecture Overview

```mermaid
graph TD
    User([User]) <-->|Voice / Text| Frontend[React 19 + TypeScript + Vite + Tailwind]
    
    subgraph Frontend Layer
        WebSpeech[Web Speech API (te-IN / en-IN)]
        WebAudio[Web Audio API (AnalyserNode)]
        Avatar[SVG/CSS Animated Character]
        State[Voice State Machine: Idle ➔ Listening ➔ Thinking ➔ Speaking]
    end

    Frontend <-->|REST API / Axios Interceptors| Backend[FastAPI Backend Server]

    subgraph Backend Layer
        Auth[JWT & Refresh Token Service + Phone OTP]
        ChatEngine[Context Builder + Memory Injector]
        Gemini[Google Gemini 3.6 Flash]
        VoiceEngine[TTS Engine: gTTS / EdgeTTS + STT Fallback]
        MemoryExtractor[Memory Extraction Pipeline]
    end

    Backend <-->|SQLAlchemy 2.0 ORM| MySQL[(MySQL 8.0 sakhi_ai utf8mb4)]
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Frontend** | React 19, TypeScript, Vite 8, Tailwind CSS v4, Lucide React, React Router v7 |
| **Voice / Audio** | Web Speech API, MediaRecorder API, Web Audio API (`AnalyserNode`) |
| **Backend** | Python 3.12, FastAPI, Uvicorn, Pydantic v2 |
| **Database & ORM** | MySQL 8.0, SQLAlchemy 2.0, PyMySQL, Alembic Migrations |
| **AI Engine** | Google Gemini (`gemini-3.6-flash` via official `google-genai` SDK) |
| **Speech Engine** | gTTS (Authentic Telugu Unicode / Tanglish synthesis), EdgeTTS abstraction |
| **Security** | Passcode bcrypt hashing, PyJWT, OTP verification hashing, CORS protection |

---

## 📁 Project Directory Structure

```text
Sakhi_AI/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI Application & Lifespan handler
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic BaseSettings & Environment variables
│   │   │   └── security.py          # Password hashing, JWT & Refresh token tokens
│   │   ├── database/
│   │   │   ├── database.py          # SQLAlchemy Engine & SessionLocal pool
│   │   │   └── models.py            # 8 MySQL Models (User, FriendProfile, etc.)
│   │   ├── schemas/                 # Pydantic DTOs for Auth, Chat, Voice, Memories
│   │   ├── api/                     # REST API Routers (auth, users, friend, chat, etc.)
│   │   ├── ai/
│   │   │   ├── gemini.py            # Google Gemini AI Provider wrapper
│   │   │   ├── prompts.py           # Sakhi System Persona & Prompts
│   │   │   ├── memory.py            # Long-term memory extractor & filter
│   │   │   └── service.py           # Context assembly & Conversation titles
│   │   ├── voice/
│   │   │   ├── tts.py               # Telugu & English multi-voice speech synthesis
│   │   │   ├── stt.py               # Multimodal audio transcription fallback
│   │   │   └── service.py           # Voice options & audio preview generation
│   │   ├── services/
│   │   └── utils/
│   ├── migrations/                  # Alembic migration scripts
│   ├── tests/                       # Pytest test suite (11 unit & integration tests)
│   ├── requirements.txt
│   ├── alembic.ini
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   │   ├── avatar/              # AnimatedCharacter (SVG multi-state avatar)
│   │   │   ├── voice/               # MicrophoneButton, VoiceWaveform
│   │   │   ├── chat/                # MessageBubble, ChatPanel (slide-out/drawer)
│   │   │   └── modals/              # Modal, ConfirmDialog, BottomSheet
│   │   ├── context/                 # AuthContext, VoiceContext, ToastContext
│   │   ├── pages/                   # Landing, Login, Register, Onboarding, Home, etc.
│   │   ├── services/                # Axios API services (auth, chat, voice, memory)
│   │   ├── types/                   # TypeScript interfaces
│   │   ├── App.tsx                  # Router & Route guards
│   │   ├── main.tsx
│   │   └── index.css                # Glassmorphic utilities & animations
│   ├── package.json
│   ├── vite.config.ts
│   └── tsconfig.json
├── README.md
└── docker-compose.yml
```

---

## 🚀 Getting Started

### 1. Prerequisites
- **Node.js**: v18.0.0 or higher
- **Python**: v3.11 or v3.12
- **MySQL Server**: 8.0+ running on `localhost:3306`

---

### 2. MySQL Database Setup

Log into MySQL shell or MySQL Workbench:
```sql
CREATE DATABASE sakhi_ai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

### 3. Backend Setup

1. Open terminal in `backend/`:
   ```bash
   cd backend
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure Environment Variables (`backend/.env`):
   ```env
   ENVIRONMENT=development
   DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/sakhi_ai
   GEMINI_API_KEY=YOUR_GEMINI_API_KEY
   JWT_SECRET=your-super-secure-jwt-secret-key-min-32-chars
   JWT_REFRESH_SECRET=your-super-secure-refresh-jwt-secret-key
   GOOGLE_CLIENT_ID=optional-google-client-id
   GOOGLE_CLIENT_SECRET=optional-google-client-secret
   STT_API_KEY=optional
   TTS_API_KEY=optional
   ```
   *(Note: If your MySQL password contains special characters like `@` or `!`, URL-encode them, e.g., `%40` and `%21`)*

4. Run Database Migrations:
   ```bash
   alembic upgrade head
   ```

5. Run Automated Tests:
   ```bash
   pytest
   ```
   *(All 11 tests should pass: database CRUD, cascades, user isolation, JWT revocation, chat AI, and voice audio streams).*

6. Start Backend Server:
   ```bash
   python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   Check health at `http://127.0.0.1:8000/health`.

---

### 4. Frontend Setup

1. Open another terminal in `frontend/`:
   ```bash
   cd frontend
   npm install
   ```

2. Build and Typecheck:
   ```bash
   npm run build
   ```

3. Start Development Server:
   ```bash
   npm run dev -- --host 127.0.0.1 --port 5173
   ```
   Open `http://127.0.0.1:5173/` in your browser.

---

## 🎙️ Voice & Audio Flow

1. **Speech-to-Text (STT)**:
   - Primary: Browser **Web Speech API** targeting `te-IN` (Telugu) and `en-IN` (Indian English).
   - Fallback: Direct audio recording sent via `POST /api/voice/transcribe` processed by Gemini Multimodal Audio.
2. **AI Inference**:
   - Backend context builder injects user preferences, friend name, conversation history, and long-term memory into the Sakhi Persona prompt.
   - Response generated in natural Telugu / Tanglish.
3. **Text-to-Speech (TTS)**:
   - Strips markdown and generates clean audio stream via `POST /api/voice/synthesize`.
   - Audio synthesized in Telugu (`te`) or Indian English (`en-in`).
4. **Playback & Animation**:
   - Audio decoded through the browser's `AudioContext`.
   - `AnalyserNode` computes live RMS amplitude/frequency, driving dynamic mouth movements on the 2D SVG avatar.
5. **Instant Interruption**:
   - Clicking the mic button during playback stops audio immediately, resets the audio node, cancels animation, and switches straight to listening mode.

---

## 🔒 Security & User Isolation

- **Zero Data Leakage**: User A cannot read, update, or delete User B's conversations, messages, memories, or settings. Ownership is enforced at the database query level (`conversation.user_id == current_user.id`).
- **Server-Side Session Invalidation**: Refresh tokens are stored as sha256 hashes in MySQL. Logging out explicitly revokes the refresh token in MySQL.
- **OTP Brute-Force Protection**: 6-digit phone OTPs are hashed using SHA-256 with rate limiting (maximum 5 attempts) and an expiration window (5 minutes).
- **Environment Isolation**: API keys (`GEMINI_API_KEY`) and database credentials are kept strictly in backend `.env`.

---

## 🧪 Verification & Acceptance Checklist

| Requirement | Implementation & Status |
| :--- | :--- |
| **MySQL 8.0 utf8mb4** | ✅ Tested & verified with `sakhi_ai` database |
| **FastAPI Backend** | ✅ Running on `http://127.0.0.1:8000` |
| **React 19 + Vite Frontend** | ✅ Running on `http://127.0.0.1:5173` |
| **All Automated Tests** | ✅ `pytest` passes 11/11 tests |
| **TypeScript Compilation** | ✅ `npm run build` succeeds with zero errors |
| **Interactive Onboarding** | ✅ 6-step personalized setup with voice preview |
| **Telugu / Tanglish Chat** | ✅ Tested casual, academic (7-marks), and coding answers |
| **Long-Term Memory** | ✅ View, delete, clear, and context injection |
| **Voice Synthesis** | ✅ Real audio playback with frequency-based lip sync |
| **No Browser Alerts** | ✅ 100% custom accessible modals & toast notifications |

---

## 📄 License
MIT License. Built with passion for voice-first Telugu conversational AI.
