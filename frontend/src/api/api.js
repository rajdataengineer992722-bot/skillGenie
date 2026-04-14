function resolveBaseUrl() {
  const configured = import.meta.env.VITE_API_BASE_URL?.replace(/\/$/, "");
  if (configured) {
    return configured;
  }

  if (typeof window !== "undefined") {
    const host = window.location.hostname || "127.0.0.1";
    return `http://${host}:8000`;
  }

  return "http://127.0.0.1:8000";
}

const BASE_URL = resolveBaseUrl();

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      detail = payload.detail || payload.message || detail;
    } catch {
      const text = await response.text();
      detail = text || detail;
    }
    const error = new Error(detail);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

export function checkHealth() {
  return request("/health");
}

export function registerUser(payload) {
  return request("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function loginUser(payload) {
  return request("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function loginWithGoogle(credential) {
  return request("/auth/google", {
    method: "POST",
    body: JSON.stringify({ credential }),
  });
}

export function requestPasswordReset(email) {
  return request("/auth/password-reset/request", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function confirmPasswordReset(token, password) {
  return request("/auth/password-reset/confirm", {
    method: "POST",
    body: JSON.stringify({ token, password }),
  });
}

export function getCurrentUser() {
  return request("/auth/me");
}

export function logoutUser() {
  return request("/auth/logout", {
    method: "POST",
  });
}

export function generatePlanForUser(form) {
  return request("/plan", {
    method: "POST",
    body: JSON.stringify({
      role: form.role,
      goal: form.goal,
      knowledge_level: form.knowledgeLevel,
      department: form.department || "",
      business_context: form.businessContext || "",
      past_learning: form.pastLearning || "",
    }),
  });
}

export function sendChatMessageForUser(message) {
  return request("/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function getDashboard() {
  return request("/dashboard");
}

export function updateProgress(planId, completedSteps, hoursSpent) {
  return request(`/progress/${planId}`, {
    method: "PATCH",
    body: JSON.stringify({
      completed_steps: completedSteps,
      hours_spent: hoursSpent,
    }),
  });
}
