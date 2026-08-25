"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const {
  escapeHtml,
  renderAgentDetailHtml,
  renderDashboardHtml,
} = require("../src/webviews");

test("escapeHtml neutralise les caractères actifs dans du HTML", () => {
  assert.equal(
    escapeHtml(`<img src=x onerror="alert('x')"> &`),
    "&lt;img src=x onerror=&quot;alert(&#39;x&#39;)&quot;&gt; &amp;",
  );
});

test("le dashboard applique une CSP stricte et échappe les données API", () => {
  const malicious = `<script>alert("x")</script>`;
  const html = renderDashboardHtml({
    state: "ready",
    nonce: "nonce-test",
    agents: [
      {
        id: 1,
        name: malicious,
        model: `mistral&<x>`,
        description: `"onmouseover=alert(1)`,
      },
    ],
  });

  assert.match(html, /default-src 'none'; style-src 'nonce-nonce-test';/);
  assert.match(html, /<style nonce="nonce-test">/);
  assert.doesNotMatch(html, /<script>alert/);
  assert.match(html, /&lt;script&gt;alert\(&quot;x&quot;\)&lt;\/script&gt;/);
  assert.match(html, /mistral&amp;&lt;x&gt;/);
});

test("les webviews suivent automatiquement les variables du thème VS Code", () => {
  const html = renderDashboardHtml({ state: "empty", nonce: "theme-nonce" });

  assert.match(html, /color: var\(--vscode-foreground\)/);
  assert.match(html, /background: var\(--vscode-editor-background\)/);
  assert.match(html, /background: var\(--vscode-sideBar-background\)/);
  assert.match(html, /color: var\(--vscode-descriptionForeground\)/);
});

test("le dashboard rend les états vide et erreur", () => {
  const empty = renderDashboardHtml({ state: "empty", nonce: "n" });
  const error = renderDashboardHtml({
    state: "error",
    error: "Connexion <refusée>",
    nonce: "n",
  });

  assert.match(empty, /Aucun agent disponible/);
  assert.match(error, /Impossible de charger les agents/);
  assert.match(error, /Connexion &lt;refusée&gt;/);
});

test("le détail affiche les champs et échappe également les données", () => {
  const html = renderAgentDetailHtml({
    nonce: "detail-nonce",
    agent: {
      id: 9,
      name: "Agent <admin>",
      model: "gpt-4",
      description: "A&B",
      is_active: false,
    },
  });

  assert.match(html, /Agent &lt;admin&gt;/);
  assert.match(html, /A&amp;B/);
  assert.match(html, /Inactif/);
  assert.doesNotMatch(html, /<script/);
});
