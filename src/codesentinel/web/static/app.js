const $ = (id) => document.getElementById(id);

async function runReview() {
  const code = $("code").value;
  const status = $("status");
  if (!code.trim()) {
    status.textContent = "Paste some code first.";
    return;
  }

  $("submit").disabled = true;
  status.textContent = "Reviewing...";

  try {
    const res = await fetch("/api/review", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        code,
        language: $("language").value,
        provider: $("provider").value || null,
        use_llm: $("use_llm").checked,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const result = await res.json();
    renderResult(result);
    status.textContent = "Done.";
    loadHistory();
  } catch (e) {
    status.textContent = `Error: ${e.message}`;
  } finally {
    $("submit").disabled = false;
  }
}

function renderResult(result) {
  $("result-panel").hidden = false;
  $("result-summary").innerHTML =
    `<strong>${result.score}/100 — ${escapeHtml(result.verdict)}</strong>` +
    `<span class="score-sub">${result.findings.length} findings · ${result.duration_seconds}s</span>`;

  const body = $("findings-body");
  body.innerHTML = "";
  for (const f of result.findings) {
    const tr = document.createElement("tr");
    tr.className = `sev-${f.severity}`;
    tr.innerHTML = `
      <td><span class="sev-badge">${f.severity}</span></td>
      <td>${f.category}</td>
      <td>${f.rule_id}</td>
      <td>${f.line ?? "-"}</td>
      <td>${escapeHtml(f.message)}</td>
    `;
    body.appendChild(tr);
  }

  const llmBlock = $("llm-block");
  if (result.llm_summary) {
    llmBlock.innerHTML = `<h3>LLM Insight (${result.llm_provider ?? "n/a"})</h3><pre>${escapeHtml(result.llm_summary)}</pre>`;
  } else {
    llmBlock.innerHTML = "";
  }
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s ?? "";
  return div.innerHTML;
}

async function loadHistory() {
  const res = await fetch("/api/history");
  const rows = await res.json();
  const body = $("history-body");
  body.innerHTML = "";
  for (const r of rows) {
    const tr = document.createElement("tr");
    const when = new Date(r.created_at * 1000).toLocaleString();
    tr.innerHTML = `<td>${r.id}</td><td>${escapeHtml(r.target)}</td><td>${r.language}</td><td>${r.score}</td><td>${r.verdict}</td><td>${when}</td>`;
    body.appendChild(tr);
  }
}

$("submit").addEventListener("click", runReview);
loadHistory();
