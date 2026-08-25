"use strict";

const crypto = require("node:crypto");

function renderDashboardHtml({ state, agents = [], error = "", nonce = createNonce() }) {
  let content;

  if (state === "loading") {
    content = renderMessage("Chargement…", "Connexion à l’API Agent World.");
  } else if (state === "error") {
    content = renderMessage(
      "Impossible de charger les agents",
      error || "Une erreur inconnue est survenue.",
      "error",
    );
  } else if (state === "empty" || agents.length === 0) {
    content = renderMessage(
      "Aucun agent disponible",
      "Créez un agent avec l’API ou le CLI, puis utilisez la commande d’actualisation.",
    );
  } else {
    content = `<section class="grid" aria-label="Liste des agents">${agents
      .map(renderAgentCard)
      .join("")}</section>`;
  }

  return documentHtml({
    nonce,
    title: "Agent World — Dashboard",
    heading: "Agents",
    intro:
      "Vue d’ensemble des agents. Sélectionnez un agent dans l’Activity Bar pour ouvrir son détail.",
    content,
  });
}

function renderAgentDetailHtml({ agent, nonce = createNonce() }) {
  if (!agent || typeof agent !== "object" || Array.isArray(agent)) {
    return documentHtml({
      nonce,
      title: "Agent World — Détail",
      heading: "Détail de l’agent",
      intro: "",
      content: renderMessage(
        "Agent indisponible",
        "Actualisez la vue Agents, puis sélectionnez de nouveau un agent.",
        "error",
      ),
    });
  }

  const name = displayText(agent.name, agent.id ? `Agent #${agent.id}` : "Agent sans nom");
  const active = agent.is_active === false ? "Inactif" : "Actif";
  const content = `
    <section class="detail" aria-label="Informations de l’agent">
      <dl>
        ${detailRow("Identifiant", displayText(agent.id, "—"))}
        ${detailRow("Nom", name)}
        ${detailRow("Modèle", displayText(agent.model, "Non renseigné"))}
        ${detailRow("Statut", active)}
        ${detailRow("Description", displayText(agent.description, "Aucune description"))}
        ${detailRow("Créé le", displayText(agent.created_at, "Non renseigné"))}
        ${detailRow("Modifié le", displayText(agent.updated_at, "Non renseigné"))}
      </dl>
    </section>`;

  return documentHtml({
    nonce,
    title: `Agent World — ${name}`,
    heading: name,
    intro: "Détail de l’agent sélectionné.",
    content,
  });
}

function renderAgentCard(agent) {
  const name = displayText(agent.name, agent.id ? `Agent #${agent.id}` : "Agent sans nom");
  const model = displayText(agent.model, "Modèle non renseigné");
  const description = displayText(agent.description, "Aucune description");
  const isInactive = agent.is_active === false;

  return `
    <article class="card">
      <div class="card-heading">
        <h2>${escapeHtml(name)}</h2>
        <span class="status ${isInactive ? "inactive" : "active"}">${
          isInactive ? "Inactif" : "Actif"
        }</span>
      </div>
      <p class="model">${escapeHtml(model)}</p>
      <p>${escapeHtml(description)}</p>
    </article>`;
}

function renderMessage(title, message, kind = "info") {
  return `
    <section class="message ${kind}" role="status">
      <h2>${escapeHtml(title)}</h2>
      <p>${escapeHtml(message)}</p>
    </section>`;
}

function detailRow(label, value) {
  return `<div><dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value)}</dd></div>`;
}

function documentHtml({ nonce, title, heading, intro, content }) {
  const safeNonce = escapeHtml(nonce);
  return `<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'nonce-${safeNonce}';">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${escapeHtml(title)}</title>
  <style nonce="${safeNonce}">
    :root { color-scheme: light dark; }
    body {
      box-sizing: border-box;
      max-width: 1100px;
      margin: 0 auto;
      padding: 28px;
      color: var(--vscode-foreground);
      background: var(--vscode-editor-background);
      font-family: var(--vscode-font-family);
      font-size: var(--vscode-font-size);
    }
    *, *::before, *::after { box-sizing: inherit; }
    h1 { margin: 0 0 8px; font-size: 1.8rem; }
    h2 { margin: 0; font-size: 1.08rem; }
    .intro { margin: 0 0 24px; color: var(--vscode-descriptionForeground); }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 14px; }
    .card, .detail, .message {
      padding: 18px;
      border: 1px solid var(--vscode-panel-border);
      border-radius: 6px;
      background: var(--vscode-sideBar-background);
    }
    .card-heading { display: flex; align-items: start; justify-content: space-between; gap: 12px; }
    .card p { margin: 12px 0 0; overflow-wrap: anywhere; }
    .card .model { color: var(--vscode-descriptionForeground); }
    .status { flex: none; padding: 2px 7px; border-radius: 999px; font-size: .82rem; }
    .status.active { color: var(--vscode-testing-iconPassed); border: 1px solid currentColor; }
    .status.inactive { color: var(--vscode-disabledForeground); border: 1px solid currentColor; }
    .message { max-width: 650px; }
    .message p { margin: 10px 0 0; }
    .message.error { border-color: var(--vscode-inputValidation-errorBorder); }
    dl { margin: 0; }
    dl div { display: grid; grid-template-columns: minmax(110px, 180px) 1fr; gap: 16px; padding: 10px 0; }
    dl div + div { border-top: 1px solid var(--vscode-panel-border); }
    dt { color: var(--vscode-descriptionForeground); font-weight: 600; }
    dd { margin: 0; overflow-wrap: anywhere; white-space: pre-wrap; }
    @media (max-width: 520px) {
      body { padding: 18px; }
      dl div { grid-template-columns: 1fr; gap: 4px; }
    }
  </style>
</head>
<body>
  <header>
    <h1>${escapeHtml(heading)}</h1>
    ${intro ? `<p class="intro">${escapeHtml(intro)}</p>` : ""}
  </header>
  <main>${content}</main>
</body>
</html>`;
}

function displayText(value, fallback = "") {
  if (value === undefined || value === null || String(value).trim() === "") {
    return fallback;
  }
  return String(value).trim();
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function createNonce() {
  return crypto.randomBytes(18).toString("base64");
}

module.exports = {
  createNonce,
  displayText,
  escapeHtml,
  renderAgentDetailHtml,
  renderDashboardHtml,
};
