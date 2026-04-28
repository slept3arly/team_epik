document.addEventListener("DOMContentLoaded", () => {
  const loginTab = document.getElementById("loginTab");
  const signUpTab = document.getElementById("signUpTab");
  const loginPanel = document.getElementById("loginPanel");
  const signUpPanel = document.getElementById("signUpPanel");
  const loginForm = document.getElementById("loginForm");
  const signUpForm = document.getElementById("signUpForm");
  const messageBox = document.getElementById("authMessage");

  if (!loginForm || !signUpForm || !loginTab || !signUpTab || !loginPanel || !signUpPanel) {
    return;
  }

  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";

  const setMessage = (message, tone = "muted") => {
    if (!messageBox) {
      return;
    }
    messageBox.textContent = message;
    messageBox.dataset.tone = tone;
  };

  const activatePanel = (panel) => {
    const isLogin = panel === "login";
    loginTab.classList.toggle("is-active", isLogin);
    signUpTab.classList.toggle("is-active", !isLogin);
    loginPanel.classList.toggle("is-active", isLogin);
    signUpPanel.classList.toggle("is-active", !isLogin);
    setMessage("");
  };

  loginTab.addEventListener("click", () => activatePanel("login"));
  signUpTab.addEventListener("click", () => activatePanel("signup"));

  const readFormValue = (id) => document.getElementById(id)?.value.trim() || "";

  const submitJson = async (url, payload) => {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
      body: JSON.stringify(payload),
    });

    const data = await response.json().catch(() => ({}));
    if (!response.ok) {
      throw new Error(data.message || "Request failed.");
    }
    return data;
  };

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const data = await submitJson("/login", {
        identity: readFormValue("loginIdentity"),
        password: readFormValue("loginPassword"),
      });
      setMessage(data.message || "Logged in successfully.", "success");
      window.setTimeout(() => {
        window.location.assign("/");
      }, 300);
    } catch (error) {
      setMessage(error.message, "danger");
    }
  });

  signUpForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const password = readFormValue("signUpPassword");
      const confirmPassword = readFormValue("signUpConfirmPassword");
      if (password !== confirmPassword) {
        throw new Error("Passwords do not match.");
      }

      const data = await submitJson("/signup", {
        username: readFormValue("signUpUsername"),
        email: readFormValue("signUpEmail"),
        password,
      });
      setMessage(data.message || "Account created.", "success");
      window.setTimeout(() => activatePanel("login"), 300);
    } catch (error) {
      setMessage(error.message, "danger");
    }
  });
});

