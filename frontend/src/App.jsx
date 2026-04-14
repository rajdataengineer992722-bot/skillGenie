import { startTransition, useEffect, useMemo, useState } from "react";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import StatsCards from "./components/StatsCards";
import LearningPath from "./components/LearningPath";
import Assistant from "./components/Assistant";
import Recommendations from "./components/Recommendations";
import Progress from "./components/Progress";
import AuthPanel from "./components/AuthPanel";
import ActivityFeed from "./components/ActivityFeed";
import FlashStack from "./components/FlashStack";
import {
  checkHealth,
  confirmPasswordReset,
  generatePlanForUser,
  getCurrentUser,
  getDashboard,
  loginUser,
  loginWithGoogle,
  logoutUser,
  requestPasswordReset,
  registerUser,
  sendChatMessageForUser,
  updateProgress,
} from "./api/api";

const INITIAL_FORM = {
  role: "Frontend Developer",
  goal: "Build production-ready React projects and improve system design skills",
  knowledgeLevel: "beginner",
  department: "Engineering",
  businessContext: "",
  pastLearning: "",
};

const EMPTY_METRICS = {
  total_plans: 0,
  completed_steps: 0,
  total_steps: 0,
  hours_spent: 0,
  best_progress: 0,
  focus_score: 0,
  total_messages: 0,
};

function parsePlan(planText) {
  return String(planText || "")
    .split(/\n+/)
    .map((line) => line.replace(/^\s*[-*]\s*/, "").trim())
    .filter(Boolean)
    .map((line, index) => {
      const match = line.match(/^(Week\s*\d+)\s*[:.-]?\s*(.*)$/i);
      return {
        id: `${index}-${line.slice(0, 16)}`,
        title: match?.[1] || `Step ${index + 1}`,
        detail: match?.[2] || line,
      };
    });
}

function buildRecommendations(role, goal, steps, metrics) {
  const seed = `${role} ${goal} ${steps.map((step) => step.detail).join(" ")}`;
  const tags = Array.from(
    new Set(
      seed
        .split(/[^a-zA-Z0-9+#.]+/)
        .map((word) => word.trim())
        .filter((word) => word.length > 3)
    )
  ).slice(0, 4);

  const fallback = ["Projects", "Roadmaps", "Practice", "Interview Prep"];
  const baseItems = (tags.length ? tags : fallback).map((tag, index) => ({
    id: `${tag}-${index}`,
    title: tag,
    description:
      index === 0
        ? "Focus on this area first to create momentum."
        : "Use this as your next supporting topic.",
    meta: index === 0 ? `${metrics.focus_score || 0}% current focus score` : undefined,
    action:
      index === 0
        ? `Turn ${tag} into your next 45-minute study block.`
        : `Use ${tag} as the next supporting topic after your main task.`,
  }));

  if ((metrics.total_messages || 0) < 3) {
    baseItems.push({
      id: "assistant-habit",
      title: "Ask the assistant daily",
      description: "Use the coach for faster feedback loops and better prioritization.",
      meta: "Build a stronger learning rhythm",
      action: "Ask for a 7-day sprint or one realistic project brief.",
    });
  }

  return baseItems.slice(0, 4);
}

function buildAssistantPrompts(role, goal, planText) {
  const normalizedRole = role?.trim() || "my target role";
  const normalizedGoal = goal?.trim() || "my current goal";
  const hasPlan = String(planText || "").trim().length > 0;

  return [
    `Give me a 7-day sprint for becoming a stronger ${normalizedRole}`,
    `What is the best project to prove I can ${normalizedGoal}?`,
    hasPlan
      ? "Turn my current roadmap into a realistic daily schedule"
      : `Make a beginner-friendly first week plan for ${normalizedGoal}`,
  ];
}

export default function App() {
  const [user, setUser] = useState(null);
  const [sessionReady, setSessionReady] = useState(false);
  const [authMode, setAuthMode] = useState("login");
  const [authForm, setAuthForm] = useState({
    full_name: "",
    email: "",
    password: "",
    reset_token: "",
  });
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState("");
  const [resetMessage, setResetMessage] = useState("");
  const [form, setForm] = useState(INITIAL_FORM);
  const [planText, setPlanText] = useState("");
  const [selectedPlanId, setSelectedPlanId] = useState(null);
  const [structuredPlan, setStructuredPlan] = useState(null);
  const [planLoading, setPlanLoading] = useState(false);
  const [planError, setPlanError] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState("");
  const [plans, setPlans] = useState([]);
  const [messages, setMessages] = useState([]);
  const [metrics, setMetrics] = useState(EMPTY_METRICS);
  const [activity, setActivity] = useState([]);
  const [apiStatus, setApiStatus] = useState("checking");
  const [flashes, setFlashes] = useState([]);
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  function dismissFlash(id) {
    setFlashes((current) => current.filter((item) => item.id !== id));
  }

  function showFlash(message, tone = "info", title = "") {
    const id = `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
    setFlashes((current) => [...current, { id, message, tone, title }]);
    window.setTimeout(() => {
      setFlashes((current) => current.filter((item) => item.id !== id));
    }, 4800);
  }

  function clearSessionState() {
    setUser(null);
    setPlans([]);
    setMessages([]);
    setMetrics(EMPTY_METRICS);
    setActivity([]);
    setPlanText("");
    setSelectedPlanId(null);
    setStructuredPlan(null);
  }

  function focusAuthPanel() {
    window.setTimeout(() => {
      document.getElementById("insights")?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    }, 80);
  }

  function isAuthError(error) {
    const message = String(error?.message || "").toLowerCase();
    return (
      error?.status === 401 ||
      message.includes("authentication required") ||
      message.includes("invalid or expired session")
    );
  }

  function handleProtectedActionError(error, fallbackMessage) {
    if (isAuthError(error)) {
      clearSessionState();
      setAuthMode("login");
      setAuthError("Your session expired or the browser blocked the auth cookie. Please sign in again.");
      showFlash(
        "Your session expired or was not saved. Sign in again to keep using protected features.",
        "error",
        "Authentication required"
      );
      focusAuthPanel();
      return true;
    }

    showFlash(error.message || fallbackMessage, "error", "Request failed");
    return false;
  }

  useEffect(() => {
    let active = true;

    async function loadHealth() {
      try {
        await checkHealth();
        if (active) {
          setApiStatus("online");
        }
      } catch {
        if (active) {
          setApiStatus("offline");
        }
      }
    }

    loadHealth();
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!googleClientId) {
      return;
    }

    const existing = document.querySelector('script[data-google-identity="true"]');
    if (existing) {
      return;
    }

    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    script.dataset.googleIdentity = "true";
    document.head.appendChild(script);

    return () => {
      script.remove();
    };
  }, [googleClientId]);

  useEffect(() => {
    let active = true;

    async function loadSession() {
      try {
        const [{ user: currentUser }, dashboard] = await Promise.all([
          getCurrentUser(),
          getDashboard(),
        ]);
        if (!active) {
          return;
        }
        setUser(currentUser);
        setPlans(dashboard.plans || []);
        setMetrics(dashboard.metrics || {});
        setActivity(dashboard.activity || []);
        const firstPlan = (dashboard.plans || [])[0];
        setSelectedPlanId(firstPlan?.id || null);
        if (firstPlan) {
          setPlanText(firstPlan.plan_text || "");
          try {
            setStructuredPlan(firstPlan.plan_json ? JSON.parse(firstPlan.plan_json) : null);
          } catch {
            setStructuredPlan(null);
          }
          setForm((current) => ({
            ...current,
            role: firstPlan.role || current.role,
            goal: firstPlan.goal || current.goal,
            knowledgeLevel: firstPlan.knowledge_level || current.knowledgeLevel,
          }));
        }
        setMessages(
          (dashboard.messages || []).map((message) => ([
            {
              id: `prompt-${message.id}`,
              role: "user",
              content: message.prompt,
            },
            {
              id: `response-${message.id}`,
              role: "assistant",
              content: message.response,
            },
          ])).flat()
        );
      } catch {
        clearSessionState();
      } finally {
        if (active) {
          setSessionReady(true);
        }
      }
    }

    loadSession();
    return () => {
      active = false;
    };
  }, []);

  const planSteps = useMemo(() => parsePlan(planText), [planText]);
  const derivedFocusScore =
    metrics.total_steps > 0
      ? metrics.focus_score
      : (plans[0]?.progress_percent ?? Math.min(96, 60 + planSteps.length * 8));
  const derivedTotalSteps = metrics.total_steps || plans[0]?.total_steps || planSteps.length || 0;
  const derivedMessages = metrics.total_messages || Math.floor(messages.length / 2);

  const stats = useMemo(
    () => [
      { label: "Plan Steps", value: String(derivedTotalSteps), tone: "amber" },
      { label: "Chat Threads", value: String(derivedMessages), tone: "blue" },
      {
        label: "Focus Score",
        value: `${derivedFocusScore}%`,
        tone: "green",
      },
      {
        label: "API Status",
        value: apiStatus === "online" ? "Live" : apiStatus === "offline" ? "Retry" : "Syncing",
        tone: "slate",
      },
    ],
    [apiStatus, derivedFocusScore, derivedMessages, derivedTotalSteps]
  );

  const recommendations = useMemo(
    () => buildRecommendations(form.role, form.goal, planSteps, metrics),
    [form.goal, form.role, metrics, planSteps]
  );
  const assistantPrompts = useMemo(
    () => buildAssistantPrompts(form.role, form.goal, planText),
    [form.goal, form.role, planText]
  );

  const progress = useMemo(() => {
    const completed = Math.min(planSteps.length, Math.max(1, Math.ceil(planSteps.length * 0.5)));
    const total = planSteps.length || 4;
    return {
      completed,
      total,
      percent: derivedFocusScore,
      hours: metrics.hours_spent || plans.reduce((sum, plan) => sum + (plan.hours_spent || 0), 0) || total * 3,
      totalPlans: metrics.total_plans || plans.length,
      messages: derivedMessages,
      bestProgress: metrics.best_progress || 0,
      focusScore: metrics.focus_score || 0,
    };
  }, [derivedFocusScore, derivedMessages, metrics, planSteps.length, plans]);

  async function refreshDashboard() {
    const dashboard = await getDashboard();
    const nextPlans = dashboard.plans || [];
    setPlans(nextPlans);
    setMetrics(dashboard.metrics || EMPTY_METRICS);
    setActivity(dashboard.activity || []);
    const nextSelectedId = nextPlans.some((plan) => plan.id === selectedPlanId)
      ? selectedPlanId
      : (nextPlans[0]?.id || null);
    setSelectedPlanId(nextSelectedId);
    const activePlan = nextPlans.find((plan) => plan.id === nextSelectedId);
    if (activePlan) {
      setPlanText(activePlan.plan_text || "");
      try {
        setStructuredPlan(activePlan.plan_json ? JSON.parse(activePlan.plan_json) : null);
      } catch {
        setStructuredPlan(null);
      }
    } else {
      setStructuredPlan(null);
      setPlanText("");
    }
    setMessages(
      (dashboard.messages || []).map((message) => ([
        { id: `prompt-${message.id}`, role: "user", content: message.prompt },
        { id: `response-${message.id}`, role: "assistant", content: message.response },
      ])).flat()
    );
  }

  async function finalizeAuthenticatedSession(nextUser, successTitle, successMessage) {
    try {
      await refreshDashboard();
      setUser(nextUser);
      setAuthForm({ full_name: "", email: "", password: "", reset_token: "" });
      showFlash(successMessage, "success", successTitle);
      return true;
    } catch (error) {
      clearSessionState();
      setAuthMode("login");
      if (isAuthError(error)) {
        const message =
          "Sign-in succeeded, but your session cookie was blocked or not saved. For local development, set SESSION_COOKIE_SECURE=false and sign in again.";
        setAuthError(message);
        showFlash(message, "error", "Session not saved");
        focusAuthPanel();
      } else {
        const message = error.message || "Unable to finish loading your account.";
        setAuthError(message);
        showFlash(message, "error", "Authentication failed");
      }
      return false;
    }
  }

  async function handleAuthSubmit(event) {
    event.preventDefault();
    setAuthError("");
    setResetMessage("");
    setAuthLoading(true);

    if (authMode === "register" || authMode === "reset-confirm") {
      const password = authForm.password || "";
      const passwordValid =
        password.length >= 10 &&
        /[a-z]/.test(password) &&
        /[A-Z]/.test(password) &&
        /\d/.test(password);

      if (!passwordValid) {
        const message =
          "Password must be at least 10 characters and include uppercase, lowercase, and a number.";
        setAuthError(message);
        showFlash(message, "error", "Weak password");
        setAuthLoading(false);
        return;
      }
    }

    try {
      if (authMode === "login") {
        const response = await loginUser({
          email: authForm.email,
          password: authForm.password,
        });
        await finalizeAuthenticatedSession(
          response.user,
          "Signed in",
          `Welcome back, ${response.user.full_name}.`
        );
      } else if (authMode === "register") {
        const response = await registerUser(authForm);
        await finalizeAuthenticatedSession(
          response.user,
          "Registration complete",
          "Your account is ready and synced."
        );
      } else if (authMode === "reset-request") {
        const response = await requestPasswordReset(authForm.email);
        setResetMessage(
          response.reset_token
            ? `Use this reset token now: ${response.reset_token}`
            : response.message || "If the account exists, a reset token was generated."
        );
        setAuthForm((current) => ({ ...current, reset_token: response.reset_token || "" }));
        showFlash(
          response.reset_token
            ? "Reset token generated. Paste it into the next step."
            : response.message || "If the account exists, reset instructions were created.",
          "info",
          "Password reset"
        );
        if (response.reset_token) {
          setAuthMode("reset-confirm");
        }
      } else if (authMode === "reset-confirm") {
        const response = await confirmPasswordReset(authForm.reset_token, authForm.password);
        setResetMessage(response.message || "Password updated successfully.");
        setAuthMode("login");
        setAuthForm((current) => ({ ...current, password: "", reset_token: "" }));
        showFlash("Your password was updated. You can sign in now.", "success", "Password updated");
      }
    } catch (error) {
      setAuthError(error.message || "Unable to authenticate.");
      showFlash(error.message || "Unable to authenticate.", "error", "Authentication failed");
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleGoogleSignIn() {
    setAuthError("");
    setResetMessage("");

    if (!googleClientId) {
      const message = "Google sign-in is not configured yet.";
      setAuthError(message);
      showFlash(message, "error", "Google sign-in");
      return;
    }

    if (!window.google?.accounts?.id) {
      const message = "Google sign-in is not available right now.";
      setAuthError(message);
      showFlash(message, "error", "Google sign-in");
      return;
    }

    setAuthLoading(true);

    try {
      const credential = await new Promise((resolve, reject) => {
        let settled = false;
        window.google.accounts.id.initialize({
          client_id: googleClientId,
          callback: (response) => {
            if (settled) {
              return;
            }
            if (response.credential) {
              settled = true;
              resolve(response.credential);
              return;
            }
            settled = true;
            reject(new Error("Google sign-in was cancelled."));
          },
        });
        window.google.accounts.id.prompt((notification) => {
          if (
            !settled &&
            (notification.isNotDisplayed?.() || notification.isSkippedMoment?.())
          ) {
            settled = true;
            reject(new Error("Google sign-in was not completed."));
          }
        });
      });

      const response = await loginWithGoogle(credential);
      await finalizeAuthenticatedSession(
        response.user,
        "Welcome",
        `Signed in with Google as ${response.user.full_name}.`
      );
    } catch (error) {
      setAuthError(error.message || "Unable to sign in with Google.");
      showFlash(error.message || "Unable to sign in with Google.", "error", "Google sign-in failed");
    } finally {
      setAuthLoading(false);
    }
  }

  async function handleLogout() {
    try {
      await logoutUser();
    } catch {
      // Ignore logout failures and clear the local session anyway.
    }
    clearSessionState();
    setAuthMode("login");
    showFlash("You have been signed out.", "info", "Logged out");
  }

  async function handleGeneratePlan(event) {
    event.preventDefault();
    if (!user) {
      const message = "Sign in first to generate and save a learning plan.";
      setPlanError(message);
      showFlash(message, "error", "Authentication required");
      focusAuthPanel();
      return;
    }
    setPlanLoading(true);
    setPlanError("");

    try {
      const result = await generatePlanForUser(form);
      startTransition(() => {
        setPlanText(result.plan || "");
      });
      setStructuredPlan(result.structured_plan || null);
      await refreshDashboard();
      if (result.plan_record?.id) {
        setSelectedPlanId(result.plan_record.id);
      }
      showFlash("Learning plan generated and saved.", "success", "Plan ready");
    } catch (error) {
      const handledAuth = handleProtectedActionError(
        error,
        "Unable to generate a learning plan right now."
      );
      setPlanError(
        handledAuth
          ? "Please sign in again to generate a learning plan."
          : error.message || "Unable to generate a learning plan right now."
      );
    } finally {
      setPlanLoading(false);
    }
  }

  async function handleSendMessage(message) {
    const trimmed = message.trim();
    if (!trimmed) {
      return;
    }
    if (!user) {
      const notice = "Sign in first to chat with the assistant.";
      setChatError(notice);
      showFlash(notice, "error", "Authentication required");
      focusAuthPanel();
      return;
    }

    const userMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: trimmed,
    };

    setChatError("");
    setChatLoading(true);
    setMessages((current) => [...current, userMessage]);

    try {
      const result = await sendChatMessageForUser(trimmed);
      const reply = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: result.response || "I could not generate a reply.",
      };
      setMessages((current) => [...current, reply]);
    } catch (error) {
      setMessages((current) => current.filter((item) => item.id !== userMessage.id));
      const handledAuth = handleProtectedActionError(
        error,
        "Unable to reach the assistant right now."
      );
      setChatError(
        handledAuth
          ? "Your session expired. Please sign in again to continue chatting."
          : error.message || "Unable to reach the assistant right now."
      );
    } finally {
      setChatLoading(false);
    }
  }

  async function handleUpdateProgress(planId, completedSteps, hoursSpent) {
    if (!user) {
      const message = "Sign in first to update learning progress.";
      setPlanError(message);
      showFlash(message, "error", "Authentication required");
      focusAuthPanel();
      return;
    }

    try {
      await updateProgress(planId, completedSteps, hoursSpent);
      await refreshDashboard();
      showFlash("Progress updated successfully.", "success", "Progress saved");
    } catch (error) {
      const handledAuth = handleProtectedActionError(
        error,
        "Unable to update progress right now."
      );
      setPlanError(
        handledAuth
          ? "Please sign in again to update progress."
          : error.message || "Unable to update progress right now."
      );
    }
  }

  function handleSelectPlan(plan) {
    setSelectedPlanId(plan.id);
    setPlanText(plan.plan_text || "");
    try {
      setStructuredPlan(plan.plan_json ? JSON.parse(plan.plan_json) : null);
    } catch {
      setStructuredPlan(null);
    }
    setForm({
      role: plan.role,
      goal: plan.goal,
      knowledgeLevel: plan.knowledge_level || "beginner",
      department: form.department,
      businessContext: form.businessContext,
      pastLearning: form.pastLearning,
    });
  }

  const summary = user
    ? `${metrics.total_plans || 0} plans saved, ${metrics.hours_spent || 0}h invested`
    : "Create an account to sync plans, progress, and assistant history";

  return (
    <div className="app-shell">
      <FlashStack items={flashes} onDismiss={dismissFlash} />
      <Sidebar />

      <main className="dashboard" id="top">
        <Topbar
          apiStatus={apiStatus}
          user={user}
          role={form.role}
          goal={form.goal}
          knowledgeLevel={form.knowledgeLevel}
          department={form.department}
          businessContext={form.businessContext}
          pastLearning={form.pastLearning}
          summary={summary}
          onRoleChange={(role) => setForm((current) => ({ ...current, role }))}
          onGoalChange={(goal) => setForm((current) => ({ ...current, goal }))}
          onKnowledgeLevelChange={(knowledgeLevel) =>
            setForm((current) => ({ ...current, knowledgeLevel }))
          }
          onDepartmentChange={(department) => setForm((current) => ({ ...current, department }))}
          onBusinessContextChange={(businessContext) =>
            setForm((current) => ({ ...current, businessContext }))
          }
          onPastLearningChange={(pastLearning) =>
            setForm((current) => ({ ...current, pastLearning }))
          }
          onSubmit={handleGeneratePlan}
          loading={planLoading}
          onLogout={handleLogout}
        />

        <StatsCards stats={stats} />

        <section className="dashboard-grid">
          <LearningPath
            sectionId="learning-path"
            steps={planSteps}
            planText={planText}
            structuredPlan={structuredPlan}
            plans={plans}
            selectedPlanId={selectedPlanId}
            loading={planLoading}
            error={planError}
            onGenerate={handleGeneratePlan}
            onUpdateProgress={handleUpdateProgress}
            onSelectPlan={handleSelectPlan}
            canEdit={Boolean(user)}
          />
          <Assistant
            sectionId="assistant"
            messages={messages}
            loading={chatLoading}
            error={chatError}
            prompts={assistantPrompts}
            onSend={handleSendMessage}
          />
        </section>

        <section className="dashboard-grid dashboard-grid--secondary" id="insights">
          {user ? (
            <Recommendations items={recommendations} />
          ) : sessionReady ? (
            <AuthPanel
              mode={authMode}
              form={authForm}
              loading={authLoading}
              error={authError}
              resetMessage={resetMessage}
              googleEnabled={Boolean(googleClientId)}
              onModeChange={setAuthMode}
              onChange={(field, value) =>
                setAuthForm((current) => ({ ...current, [field]: value }))
              }
              onSubmit={handleAuthSubmit}
              onGoogleSignIn={handleGoogleSignIn}
            />
          ) : (
            <section className="panel auth-panel">
              <div className="skeleton-block" />
            </section>
          )}
          <Progress data={progress} />
        </section>

        <ActivityFeed sectionId="activity" items={activity} />
      </main>
    </div>
  );
}
