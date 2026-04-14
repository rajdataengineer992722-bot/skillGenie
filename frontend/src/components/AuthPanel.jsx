export default function AuthPanel({
  mode,
  form,
  loading,
  error,
  resetMessage,
  googleEnabled,
  onModeChange,
  onChange,
  onSubmit,
  onGoogleSignIn,
}) {
  const passwordHint =
    "Use at least 10 characters with uppercase, lowercase, and a number.";
  const isRegister = mode === "register";
  const isResetRequest = mode === "reset-request";
  const isResetConfirm = mode === "reset-confirm";

  return (
    <section className="panel auth-panel">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Authentication</p>
          <h2>
            {mode === "login" ? "Sign in to sync progress" : null}
            {isRegister ? "Create your account" : null}
            {isResetRequest ? "Request a password reset" : null}
            {isResetConfirm ? "Set a new password" : null}
          </h2>
        </div>
      </div>

      <form className="assistant-form" onSubmit={onSubmit}>
        {isRegister ? (
          <label>
            <span>Full name</span>
            <input
              value={form.full_name}
              onChange={(event) => onChange("full_name", event.target.value)}
              placeholder="Rohit Sharma"
            />
          </label>
        ) : null}

        <label>
          <span>Email</span>
          <input
            value={form.email}
            onChange={(event) => onChange("email", event.target.value)}
            placeholder="you@example.com"
          />
        </label>

        {!isResetRequest ? (
          <label>
            <span>{isResetConfirm ? "New password" : "Password"}</span>
            <input
              type="password"
              value={form.password}
              onChange={(event) => onChange("password", event.target.value)}
              placeholder="StrongPass123"
            />
          </label>
        ) : null}

        {isResetConfirm ? (
          <label>
            <span>Reset token</span>
            <input
              value={form.reset_token || ""}
              onChange={(event) => onChange("reset_token", event.target.value)}
              placeholder="Paste your reset token"
            />
          </label>
        ) : null}

        {!isResetRequest ? <p className="feedback">{passwordHint}</p> : null}
        {resetMessage ? <p className="feedback feedback--success">{resetMessage}</p> : null}

        {error ? <p className="feedback feedback--error">{error}</p> : null}

        <button type="submit" className="primary-button" disabled={loading}>
          {loading ? "Saving..." : null}
          {!loading && mode === "login" ? "Sign in" : null}
          {!loading && isRegister ? "Create account" : null}
          {!loading && isResetRequest ? "Generate reset token" : null}
          {!loading && isResetConfirm ? "Update password" : null}
        </button>

        {mode === "login" && googleEnabled ? (
          <button type="button" className="ghost-button" onClick={onGoogleSignIn}>
            Continue with Google
          </button>
        ) : null}
      </form>

      <div className="auth-switch">
        {mode === "login" ? (
          <>
            <span>Need an account or forgot your password?</span>
            <div className="auth-actions">
              <button
                type="button"
                className="ghost-button"
                onClick={() => onModeChange("register")}
              >
                Register
              </button>
              <button
                type="button"
                className="ghost-button"
                onClick={() => onModeChange("reset-request")}
              >
                Reset password
              </button>
            </div>
          </>
        ) : (
          <>
            <span>Want to go back?</span>
            <button
              type="button"
              className="ghost-button"
              onClick={() => onModeChange("login")}
            >
              Sign in
            </button>
          </>
        )}
      </div>
    </section>
  );
}
