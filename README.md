# SkillGenie AI

SkillGenie AI is a full-stack learning coach application with a FastAPI backend, a React frontend, SQLite persistence, session-based authentication, learning plan generation, coaching chat, and progress tracking.

## Complete Dry Code Flow

### 1. App startup

- Backend starts in `backend/main.py`.
- It loads environment variables and settings from `backend/config.py`.
- `init_db()` in `backend/database.py` creates or upgrades the SQLite tables:
  - `users`
  - `sessions`
  - `password_reset_tokens`
  - `learning_plans`
  - `chat_messages`
  - `progress_events`
- FastAPI then registers four route groups:
  - `auth`
  - `learning`
  - `chat`
  - `metrics`
- Middleware adds request IDs, logs request timing, and returns security headers.

### 2. Frontend startup

- React starts from `frontend/src/main.jsx` and renders `frontend/src/App.jsx`.
- API base URL resolution happens in `frontend/src/api/api.js`.
  - It first uses `VITE_API_BASE_URL`.
  - If that is missing, it falls back to `http://<host>:8000`.
- On initial load, `App` performs three startup actions:
  1. Calls `/health`
  2. Loads the Google sign-in script if `VITE_GOOGLE_CLIENT_ID` is present
  3. Calls `/auth/me` and `/dashboard` to restore the existing session and dashboard state

### 3. Authentication flow

- Protected backend endpoints use `get_current_user()` from `backend/dependencies.py`.
- Authentication is resolved in this order:
  1. `Authorization: Bearer <token>`
  2. Session cookie
- Token validation is handled by `get_user_by_token()` in `backend/services/auth_service.py`.

#### Register

- The frontend submits the auth form from `handleAuthSubmit()` in `frontend/src/App.jsx`.
- `registerUser()` sends `POST /auth/register`.
- The route in `backend/routes/auth.py`:
  - rate limits the request
  - checks for an existing email
  - validates password strength
  - hashes the password with PBKDF2
  - inserts the user into SQLite
  - creates a session
  - sets the session cookie

#### Login

- `loginUser()` sends `POST /auth/login`.
- The backend verifies the password hash, creates a session, and sets the cookie.

#### Google login

- The frontend requests a Google credential from the browser SDK.
- It sends that credential to `POST /auth/google`.
- The backend verifies the Google token against the configured client ID.
- It then creates or links the user and creates a session.

#### Logout

- `logoutUser()` sends `POST /auth/logout`.
- The backend deletes the session from SQLite and clears the cookie.

#### Password reset

- `POST /auth/password-reset/request` creates a reset token.
- `POST /auth/password-reset/confirm` validates the token and updates the password hash.

### 4. Learning plan generation flow

#### Frontend

- The user fills in role, goal, knowledge level, department, business context, and past learning from the top section of the UI.
- `handleGeneratePlan()` in `frontend/src/App.jsx` calls `generatePlanForUser()`.

#### API

- `generatePlanForUser()` sends `POST /plan`.
- The route is implemented in `backend/routes/learning.py`.

#### Backend processing

- The route calls `generate_learning_plan()` in `backend/services/ai_service.py`.
- If `OPENAI_API_KEY` is configured:
  - the backend sends a structured JSON prompt to OpenAI
  - OpenAI returns a structured learning roadmap
  - the response is converted into readable `plan_text` using `_plan_to_text()`
- If OpenAI is unavailable or fails:
  - the backend falls back to a deterministic roadmap generator using role and knowledge-level heuristics

#### Persistence

- The route saves the result using `create_learning_plan()` in `backend/services/tracking_service.py`.
- The stored record includes:
  - `role`
  - `goal`
  - `knowledge_level`
  - `plan_text`
  - `plan_json`
  - computed `total_steps`

#### Frontend after response

- The app updates `planText`
- The app updates `structuredPlan`
- The app calls `refreshDashboard()`
- The app selects the newly saved plan

### 5. Dashboard flow

- The frontend calls `GET /dashboard`.
- The route lives in `backend/routes/metrics.py`.
- The backend returns:
  - `metrics` from `get_dashboard_metrics()`
  - `plans` from `list_learning_plans()`
  - `messages` from `list_recent_chat_messages()`
  - `activity` from `list_recent_progress_events()`

- The frontend maps this response into:
  - stats cards
  - saved plans
  - assistant history
  - activity feed
  - progress widgets

### 6. Chat assistant flow

#### Frontend

- The user sends a message from the `Assistant` component.
- `handleSendMessage()` in `frontend/src/App.jsx`:
  - appends the user message locally
  - calls `sendChatMessageForUser()`

#### API

- `sendChatMessageForUser()` sends `POST /chat`.
- The route is implemented in `backend/routes/chat.py`.

#### Backend logic

- The backend loads the latest learning plan.
- It loads the most recent saved chat messages.
- It calls `chat_response()` in `backend/services/ai_service.py`.
- If OpenAI is available:
  - it sends system instructions
  - it includes role, goal, latest plan snapshot, and recent conversation for context
- If OpenAI is unavailable:
  - it returns a fallback coaching response

#### Persistence

- The backend saves the prompt/response pair using `save_chat_message()` in `backend/services/tracking_service.py`.

#### Frontend after response

- The assistant reply is appended to the chat state.

### 7. Progress update flow

#### Frontend

- The user updates learning progress from the `LearningPath` component.
- `handleUpdateProgress()` calls `updateProgress(planId, completedSteps, hoursSpent)`.

#### API

- `updateProgress()` sends `PATCH /progress/{plan_id}`.
- The route is implemented in `backend/routes/metrics.py`.

#### Backend

- `update_learning_plan_progress()` in `backend/services/tracking_service.py`:
  - loads the requested plan
  - clamps `completed_steps`
  - computes `progress_percent`
  - updates the `learning_plans` row
  - inserts a `progress_events` row

#### Frontend after response

- The app calls `refreshDashboard()`.
- Metrics, progress visuals, and recent activity update from persisted database state.

### 8. Data model relationships

- One `user` has many `sessions`
- One `user` has many `learning_plans`
- One `user` has many `chat_messages`
- One `learning_plan` has many `progress_events`

### 9. Frontend rendering flow

The main page in `frontend/src/App.jsx` composes these UI sections:

- `Topbar`
  - collects role, goal, level, department, business context, and past learning
  - triggers plan generation
- `StatsCards`
  - shows dashboard KPIs
- `LearningPath`
  - renders the current roadmap
  - supports saved-plan selection
  - supports progress updates
- `Assistant`
  - handles coaching chat
- `Recommendations`
  - shows derived next-topic suggestions
- `Progress`
  - shows progress summaries
- `ActivityFeed`
  - shows recent progress history
- `AuthPanel`
  - handles login, registration, password reset, and Google sign-in when signed out
- `FlashStack`
  - shows transient success and error messages

### 10. Safety and control flow

- Authentication-related routes are rate limited in `backend/rate_limiter.py`.
- Validation failures return structured `422` responses.
- Unhandled exceptions are logged and returned as `500` responses.
- Session expiry is enforced by `get_user_by_token()` in `backend/services/auth_service.py`.

### 11. End-to-end dry run example

1. The user opens the frontend.
2. React checks backend health.
3. React attempts to restore the session with `/auth/me`.
4. If no session exists, the auth UI is shown.
5. The user registers or signs in.
6. The backend creates a session cookie.
7. The frontend reloads dashboard data from `/dashboard`.
8. The user submits role and goal details.
9. The backend generates a roadmap using OpenAI or the fallback generator.
10. The learning plan is stored in SQLite.
11. The frontend renders the saved roadmap.
12. The user sends a coaching message.
13. The backend answers using the latest plan and recent chat context.
14. The chat message pair is saved in SQLite.
15. The user updates progress for a plan.
16. The backend updates the learning plan and writes a progress event.
17. The frontend refreshes the dashboard and shows updated metrics and activity.

### 12. Test flow

There is an integration-style flow test in `backend/tests/test_auth_and_progress.py` that covers:

- register
- `/auth/me`
- plan generation
- progress update
- chat
- password reset
- dashboard fetch
- logout
- unauthorized access after logout
