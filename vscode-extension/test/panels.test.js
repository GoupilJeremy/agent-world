"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const { DashboardPanel } = require("../src/panels");

test("un dashboard masqué ne déclenche pas de refresh API", async () => {
  let requestCount = 0;
  const dashboard = new DashboardPanel({}, () => ({
    getAgents: async () => {
      requestCount += 1;
      return [];
    },
  }));
  dashboard.panel = { visible: false, webview: { html: "inchangé" } };

  await dashboard.refreshIfVisible();

  assert.equal(requestCount, 0);
  assert.equal(dashboard.panel.webview.html, "inchangé");
});
