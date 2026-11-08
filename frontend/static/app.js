const KEY = "jarvis-chat-v1";

const thread = document.getElementById("thread");
const emptyEl = document.getElementById("empty");
const messagesEl = document.getElementById("messages");
const form = document.getElementById("composer");
const input = document.getElementById("input");
const sendBtn = document.getElementById("send");
const micBtn = document.getElementById("mic");
const statusEl = document.getElementById("status");
const modelEl = document.getElementById("model");
const plusBtn = document.getElementById("plus");
const menu = document.getElementById("menu");
const clearBtn = document.getElementById("clear");

const COPY_SVG = `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><rect x="8" y="8" width="11" height="11" rx="2"/><path d="M6 15H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v1"/></svg>`;
const SPEAK_SVG = `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M4 10v4h3l5 4V6L7 10H4z"/><path d="M16.5 8.5a4 4 0 0 1 0 7" stroke-linecap="round"/></svg>`;

const state = {
  messages: load(),
  busy: false,
};

function load() {
  try {
    const raw = JSON.parse(localStorage.getItem(KEY) || "[]");
    if (!Array.isArray(raw)) return [];
    return raw
      .filter((m) => m && (m.role === "user" || m.role === "assistant") && typeof m.text === "string" && !m.pending)
      .map((m) => ({
        id: String(m.id || uid()),
        role: m.role,
        text: m.text,
        summary: typeof m.summary === "string" ? m.summary : "",
        error: Boolean(m.error),
      }));
  } catch {
    return [];
  }
}

function save() {
  const keep = state.messages.filter((m) => !m.pending);
  localStorage.setItem(KEY, JSON.stringify(keep));
}

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

function iconButton(svg, label, onClick) {
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "icon-btn";
  btn.setAttribute("aria-label", label);
  btn.innerHTML = svg;
  btn.addEventListener("click", onClick);
  return btn;
}

function render() {
  const nearBottom = thread.scrollHeight - thread.scrollTop - thread.clientHeight < 120;
  emptyEl.hidden = state.messages.length > 0;
  messagesEl.replaceChildren();
  for (const m of state.messages) {
    messagesEl.append(m.role === "user" ? userNode(m) : assistantNode(m));
  }
  if (nearBottom || state.busy) thread.scrollTop = thread.scrollHeight;
}

function userNode(m) {
  const el = document.createElement("div");
  el.className = "msg-user";
  el.textContent = m.text;
  return el;
}

function assistantNode(m) {
  const wrap = document.createElement("div");
  const text = document.createElement("div");
  text.className = "msg-assistant" + (m.pending ? " pending" : "") + (m.error ? " error" : "");
  text.textContent = m.text;
  wrap.append(text);
  if (m.pending || m.error || !m.text) return wrap;

  const actions = document.createElement("div");
  actions.className = "actions";
  actions.append(
    iconButton(COPY_SVG, "Chép", async () => {
      try {
        await navigator.clipboard.writeText(m.text);
        statusEl.textContent = "Đã chép";
      } catch {
        statusEl.textContent = "Không chép được";
      }
    }),
    iconButton(SPEAK_SVG, "Nghe lại", () => replay(m.text))
  );
  wrap.append(actions);
  if (m.summary) {
    const meta = document.createElement("details");
    meta.className = "meta";
    const summary = document.createElement("summary");
    summary.textContent = "Thời gian";
    const p = document.createElement("p");
    p.textContent = m.summary;
    meta.append(summary, p);
    wrap.append(meta);
  }
  return wrap;
}

function setBusy(busy, label) {
  state.busy = busy;
  statusEl.textContent = label;
  micBtn.disabled = busy;
  sendBtn.disabled = busy;
  input.disabled = busy;
  if (!busy) input.focus();
}

function grow() {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 160) + "px";
  sendBtn.hidden = input.value.trim().length === 0;
}

async function post(url, payload) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `Lỗi ${res.status}`);
  return data;
}

async function sendText(text) {
  const user = { id: uid(), role: "user", text };
  const pending = { id: uid(), role: "assistant", text: "Đang trả lời…", pending: true };
  state.messages.push(user, pending);
  save();
  render();
  setBusy(true, "Đang trả lời…");
  try {
    const data = await post("/api/chat", { text });
    const reply = (data.assistant_text || "").trim();
    Object.assign(pending, {
      pending: false,
      text: reply || "Jarvis chưa trả lời.",
      summary: data.summary || "",
      error: !reply,
    });
  } catch (err) {
    Object.assign(pending, { pending: false, text: err.message, error: true, summary: "" });
  }
  save();
  render();
  setBusy(false, "Sẵn sàng");
}

async function listen() {
  const ghost = { id: uid(), role: "user", text: "Đang nghe…", pending: true };
  state.messages.push(ghost);
  save();
  render();
  micBtn.classList.add("hot");
  setBusy(true, "Đang nghe… im khoảng 0,6 giây thì dừng");
  try {
    const data = await post("/api/listen", {});
    const heard = (data.user_text || "").trim();
    if (!heard) {
      state.messages = state.messages.filter((m) => m.id !== ghost.id);
      state.messages.push({
        id: uid(),
        role: "assistant",
        text: "Không nhận ra giọng. Nói gần mic hơn rồi thử lại.",
        error: true,
      });
    } else {
      ghost.text = heard;
      ghost.pending = false;
      const reply = (data.assistant_text || "").trim();
      state.messages.push({
        id: uid(),
        role: "assistant",
        text: reply || "Jarvis chưa trả lời.",
        summary: data.summary || "",
        error: !reply,
      });
    }
  } catch (err) {
    state.messages = state.messages.filter((m) => m.id !== ghost.id);
    state.messages.push({ id: uid(), role: "assistant", text: err.message, error: true });
  }
  micBtn.classList.remove("hot");
  save();
  render();
  setBusy(false, "Sẵn sàng");
}

async function replay(text) {
  if (state.busy) return;
  setBusy(true, "Đang nói…");
  try {
    await post("/api/replay", { text });
  } catch (err) {
    statusEl.textContent = err.message;
    state.busy = false;
    micBtn.disabled = false;
    sendBtn.disabled = false;
    input.disabled = false;
    return;
  }
  setBusy(false, "Sẵn sàng");
}

form.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text || state.busy) return;
  input.value = "";
  grow();
  sendText(text);
});

input.addEventListener("input", grow);
input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    form.requestSubmit();
  }
});

micBtn.addEventListener("click", () => {
  if (!state.busy) listen();
});

plusBtn.addEventListener("click", (e) => {
  e.stopPropagation();
  menu.hidden = !menu.hidden;
  plusBtn.setAttribute("aria-expanded", String(!menu.hidden));
});

clearBtn.addEventListener("click", () => {
  state.messages = [];
  localStorage.removeItem(KEY);
  menu.hidden = true;
  plusBtn.setAttribute("aria-expanded", "false");
  render();
});

document.addEventListener("click", (e) => {
  if (!menu.hidden && !menu.parentElement.contains(e.target)) {
    menu.hidden = true;
    plusBtn.setAttribute("aria-expanded", "false");
  }
});

fetch("/api/health")
  .then((r) => r.json())
  .then((h) => {
    if (h.model) modelEl.textContent = h.model;
  })
  .catch(() => {
    modelEl.textContent = "offline";
  });

render();
grow();
input.focus();
