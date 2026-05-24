/**
 * Compliance Policy AI — ChatGPT-style frontend
 */

const API_BASE = window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1"
  ? "http://127.0.0.1:8000"
  : "/api";

// === State ===
let chats = JSON.parse(localStorage.getItem("compliance_chats") || "[]");
let activeChatId = null;

// === DOM ===
const sidebar = document.getElementById("sidebar");
const sidebarToggle = document.getElementById("sidebarToggle");
const chatList = document.getElementById("chatList");
const newChatBtn = document.getElementById("newChatBtn");
const chatMessages = document.getElementById("chatMessages");
const welcomeScreen = document.getElementById("welcomeScreen");
const askForm = document.getElementById("askForm");
const questionInput = document.getElementById("questionInput");
const submitBtn = document.getElementById("submitBtn");
const sendIcon = document.getElementById("sendIcon");
const btnLoader = document.getElementById("btnLoader");
const statusDot = document.getElementById("statusDot");
const sidebarModel = document.getElementById("sidebarModel");
const activeModelEl = document.getElementById("activeModel");
const modelTierEl = document.getElementById("modelTier");
const quotaText = document.getElementById("quotaText");
const quotaFill = document.getElementById("quotaFill");
const errorBanner = document.getElementById("errorBanner");
const errorText = document.getElementById("errorText");
const errorClose = document.getElementById("errorClose");
const clearAllBtn = document.getElementById("clearAllBtn");
const regulationSelect = document.getElementById("regulationSelect");

// === API ===
async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// === Chat Management ===
function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 7);
}

function saveChats() {
  localStorage.setItem("compliance_chats", JSON.stringify(chats));
}

function createNewChat() {
  const chat = {
    id: generateId(),
    title: "New Chat",
    messages: [],
    createdAt: new Date().toISOString(),
  };
  chats.unshift(chat);
  activeChatId = chat.id;
  saveChats();
  renderSidebar();
  renderChat();
}

function deleteChat(chatId) {
  chats = chats.filter((c) => c.id !== chatId);
  if (activeChatId === chatId) {
    activeChatId = chats.length > 0 ? chats[0].id : null;
  }
  saveChats();
  renderSidebar();
  renderChat();
}

function clearAllChats() {
  if (!confirm("Delete all chats? This cannot be undone.")) return;
  chats = [];
  activeChatId = null;
  saveChats();
  renderSidebar();
  renderChat();
}

function clearCurrentChat() {
  const chat = getActiveChat();
  if (!chat) return;
  chat.messages = [];
  chat.title = "New Chat";
  saveChats();
  renderSidebar();
  renderChat();
}

function getActiveChat() {
  return chats.find((c) => c.id === activeChatId) || null;
}

function switchChat(chatId) {
  activeChatId = chatId;
  renderSidebar();
  renderChat();
  // Close mobile sidebar
  sidebar.classList.remove("open");
}

// === Render Sidebar ===
function renderSidebar() {
  chatList.innerHTML = "";
  if (chats.length === 0) {
    chatList.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);font-size:0.8rem;">No chats yet</div>';
    return;
  }
  chats.forEach((chat) => {
    const item = document.createElement("div");
    item.className = "chat-item" + (chat.id === activeChatId ? " active" : "");
    item.innerHTML = `
      <svg class="chat-item-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
      <span class="chat-item-text">${escapeHtml(chat.title)}</span>
      <span class="chat-item-count">${Math.floor(chat.messages.length / 2)}</span>
      <button class="chat-item-delete" title="Delete chat">&times;</button>
    `;
    item.addEventListener("click", (e) => {
      if (e.target.closest(".chat-item-delete")) {
        deleteChat(chat.id);
        return;
      }
      switchChat(chat.id);
    });
    chatList.appendChild(item);
  });
}

// === Render Chat Messages ===
function renderChat() {
  const chat = getActiveChat();

  if (!chat || chat.messages.length === 0) {
    welcomeScreen.classList.remove("hidden");
    // Clear any messages except welcome
    const msgs = chatMessages.querySelectorAll(".message");
    msgs.forEach((m) => m.remove());
    return;
  }

  welcomeScreen.classList.add("hidden");

  // Clear and re-render
  const existingMsgs = chatMessages.querySelectorAll(".message");
  existingMsgs.forEach((m) => m.remove());

  chat.messages.forEach((msg) => {
    appendMessageToDOM(msg);
  });

  scrollToBottom();
}

function appendMessageToDOM(msg) {
  const div = document.createElement("div");
  div.className = `message ${msg.role}`;

  if (msg.role === "user") {
    div.innerHTML = `
      <div class="message-inner">
        <div class="message-avatar">You</div>
        <div class="message-content">${escapeHtml(msg.content)}</div>
      </div>
    `;
  } else {
    const modelTag = msg.model
      ? `<div class="msg-model-tag${msg.fallback ? ' fallback' : ''}">${msg.model}${msg.fallback ? ' (fallback)' : ''}</div>`
      : "";

    const sourcesHtml = msg.sources && msg.sources.length > 0
      ? `
        <button class="sources-toggle" onclick="this.classList.toggle('open');this.nextElementSibling.classList.toggle('open')">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
          ${msg.sources.length} sources
        </button>
        <div class="sources-list">
          ${msg.sources.map((s) => `
            <div class="source-card">
              ${s.score ? `<span class="source-score">Score: ${s.score}</span>` : ""}
              <div>${escapeHtml(s.text)}</div>
            </div>
          `).join("")}
        </div>
      `
      : "";

    div.innerHTML = `
      <div class="message-inner">
        <div class="message-avatar">AI</div>
        <div class="message-content">
          ${modelTag}
          <div class="markdown-body">${marked.parse(msg.content)}</div>
          ${sourcesHtml}
          <div class="msg-actions">
            <button class="msg-action-btn copy-msg-btn" data-text="${encodeURIComponent(msg.content)}">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg>
              Copy
            </button>
          </div>
        </div>
      </div>
    `;

    // Attach copy handler
    setTimeout(() => {
      const copyBtn = div.querySelector(".copy-msg-btn");
      if (copyBtn) {
        copyBtn.addEventListener("click", () => {
          navigator.clipboard.writeText(decodeURIComponent(copyBtn.dataset.text)).then(() => {
            copyBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg> Copied!`;
            copyBtn.classList.add("copied");
            setTimeout(() => {
              copyBtn.innerHTML = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1"/></svg> Copy`;
              copyBtn.classList.remove("copied");
            }, 1500);
          });
        });
      }
    }, 0);
  }

  chatMessages.appendChild(div);
}

function showThinking() {
  const div = document.createElement("div");
  div.className = "message assistant";
  div.id = "thinkingMsg";
  div.innerHTML = `
    <div class="message-inner">
      <div class="message-avatar">AI</div>
      <div class="message-content">
        <div class="thinking">
          <div class="thinking-dot"></div>
          <div class="thinking-dot"></div>
          <div class="thinking-dot"></div>
        </div>
      </div>
    </div>
  `;
  chatMessages.appendChild(div);
  scrollToBottom();
}

function removeThinking() {
  const el = document.getElementById("thinkingMsg");
  if (el) el.remove();
}

function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

// === Ask Question ===
async function askQuestion(question) {
  // Ensure we have an active chat
  if (!activeChatId) {
    createNewChat();
  }

  const chat = getActiveChat();
  welcomeScreen.classList.add("hidden");

  // Add user message
  const userMsg = { role: "user", content: question };
  chat.messages.push(userMsg);
  appendMessageToDOM(userMsg);
  scrollToBottom();

  // Update chat title from first question
  if (chat.messages.length === 1) {
    chat.title = question.length > 40 ? question.slice(0, 40) + "..." : question;
    renderSidebar();
  }

  saveChats();

  // Show loading
  submitBtn.disabled = true;
  sendIcon.classList.add("hidden");
  btnLoader.classList.remove("hidden");
  errorBanner.classList.add("hidden");
  showThinking();

  try {
    // Build chat history for context (last 3 Q&A pairs before current question)
    const historyForApi = chat.messages
      .slice(0, -1)  // exclude the user message we just added
      .slice(-6)     // last 3 pairs (6 messages)
      .map((m) => ({ role: m.role, content: m.content }));

    const data = await apiFetch("/ask", {
      method: "POST",
      body: JSON.stringify({
        question,
        regulation: regulationSelect.value,
        chat_history: historyForApi.length > 0 ? historyForApi : undefined,
      }),
    });

    removeThinking();

    // Add assistant message
    const assistantMsg = {
      role: "assistant",
      content: data.answer,
      model: data.model_used,
      fallback: data.fallback_used,
      sources: data.sources,
    };
    chat.messages.push(assistantMsg);
    appendMessageToDOM(assistantMsg);
    saveChats();
    scrollToBottom();

    // Refresh status
    refreshStatus();
  } catch (err) {
    removeThinking();
    showError(err.message);
  } finally {
    submitBtn.disabled = false;
    sendIcon.classList.remove("hidden");
    btnLoader.classList.add("hidden");
  }
}

// === Status ===
async function refreshStatus() {
  try {
    const data = await apiFetch("/status");
    statusDot.classList.add("active");
    sidebarModel.textContent = data.active_model;
    activeModelEl.textContent = data.active_model;
    modelTierEl.textContent = data.model_tier;
    modelTierEl.className = "badge" + (data.model_tier === "fallback" ? " fallback" : "");

    const pct = data.quota_percent;
    quotaText.textContent = `${pct}% used · ${data.requests_remaining.toLocaleString()} left`;
    quotaFill.style.width = `${Math.min(pct, 100)}%`;
    quotaFill.className = "quota-fill" + (pct > 80 ? " critical" : pct > 50 ? " warning" : "");
  } catch {
    statusDot.classList.remove("active");
    sidebarModel.textContent = "Offline";
    activeModelEl.textContent = "Offline";
    quotaText.textContent = "API unavailable";
  }
}

// === Helpers ===
function showError(msg) {
  errorText.textContent = msg;
  errorBanner.classList.remove("hidden");
}

function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

// === Auto-resize textarea ===
questionInput.addEventListener("input", () => {
  questionInput.style.height = "auto";
  questionInput.style.height = Math.min(questionInput.scrollHeight, 150) + "px";
});

// === Event Listeners ===
askForm.addEventListener("submit", (e) => {
  e.preventDefault();
  const q = questionInput.value.trim();
  if (q) {
    askQuestion(q);
    questionInput.value = "";
    questionInput.style.height = "auto";
  }
});

// Enter to send, Shift+Enter for newline
questionInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    askForm.dispatchEvent(new Event("submit"));
  }
});

document.querySelectorAll(".sample-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    askQuestion(btn.dataset.q);
  });
});

newChatBtn.addEventListener("click", createNewChat);

clearAllBtn.addEventListener("click", clearAllChats);

// Update sample questions when regulation changes
const SAMPLE_QUESTIONS = {
  hipaa: [
    { label: "What is PHI?", q: "What is Protected Health Information (PHI)?" },
    { label: "Breach notification", q: "What are the HIPAA breach notification requirements?" },
    { label: "Security safeguards", q: "What are the HIPAA Security Rule safeguards?" },
    { label: "HIPAA penalties", q: "What are the penalties for HIPAA violations?" },
  ],
  gdpr: [
    { label: "Right to erasure", q: "What is the right to erasure under GDPR?" },
    { label: "Breach notification", q: "What are the data breach notification requirements?" },
    { label: "Lawful bases", q: "What are the lawful bases for processing personal data?" },
    { label: "Data subject rights", q: "What rights do data subjects have under GDPR?" },
  ],
};

function updateSampleQuestions() {
  const reg = regulationSelect.value;
  const questions = SAMPLE_QUESTIONS[reg] || SAMPLE_QUESTIONS.hipaa;
  const container = document.querySelector(".sample-questions");
  if (!container) return;
  container.innerHTML = questions.map((item) => `
    <button class="sample-btn" data-q="${escapeHtml(item.q)}">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/></svg>
      ${escapeHtml(item.label)}
    </button>
  `).join("");
  // Re-attach click handlers
  container.querySelectorAll(".sample-btn").forEach((btn) => {
    btn.addEventListener("click", () => askQuestion(btn.dataset.q));
  });
}

regulationSelect.addEventListener("change", updateSampleQuestions);

sidebarToggle.addEventListener("click", () => {
  sidebar.classList.toggle("open");
});

errorClose.addEventListener("click", () => {
  errorBanner.classList.add("hidden");
});

// === Init ===
if (chats.length > 0) {
  activeChatId = chats[0].id;
}
renderSidebar();
renderChat();
refreshStatus();
refreshStatus();
setInterval(() => { refreshStatus(); }, 30000);
