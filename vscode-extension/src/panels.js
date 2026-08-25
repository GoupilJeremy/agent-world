"use strict";

const { renderAgentDetailHtml, renderDashboardHtml } = require("./webviews");

class DashboardPanel {
  constructor(vscode, getClient) {
    this.vscode = vscode;
    this.getClient = getClient;
    this.panel = undefined;
    this.panelDisposable = undefined;
    this.requestVersion = 0;
  }

  async open() {
    if (!this.panel) {
      this.panel = this.vscode.window.createWebviewPanel(
        "agentWorld.dashboard",
        "Agent World — Dashboard",
        this.vscode.ViewColumn.One,
        {
          enableScripts: false,
          retainContextWhenHidden: false,
          localResourceRoots: [],
        },
      );
      this.panelDisposable = this.panel.onDidDispose(() => {
        this.requestVersion += 1;
        this.panel = undefined;
        this.panelDisposable = undefined;
      });
    } else {
      this.panel.reveal(this.vscode.ViewColumn.One);
    }

    await this.refreshIfVisible();
  }

  async refreshIfVisible() {
    if (!this.panel || !this.panel.visible) {
      return;
    }

    const currentRequest = ++this.requestVersion;
    this.panel.webview.html = renderDashboardHtml({ state: "loading" });

    try {
      const agents = await this.getClient().getAgents();
      if (!this.panel || currentRequest !== this.requestVersion) {
        return;
      }
      const validAgents = agents.filter(
        (agent) => agent && typeof agent === "object" && !Array.isArray(agent),
      );
      this.panel.webview.html = renderDashboardHtml({
        state: validAgents.length ? "ready" : "empty",
        agents: validAgents,
      });
    } catch (error) {
      if (!this.panel || currentRequest !== this.requestVersion) {
        return;
      }
      this.panel.webview.html = renderDashboardHtml({
        state: "error",
        error: errorMessage(error),
      });
    }
  }

  dispose() {
    this.requestVersion += 1;
    const panel = this.panel;
    this.panel = undefined;
    if (panel) {
      panel.dispose();
    }
    if (this.panelDisposable) {
      this.panelDisposable.dispose();
      this.panelDisposable = undefined;
    }
  }
}

class AgentDetailPanel {
  constructor(vscode) {
    this.vscode = vscode;
    this.panel = undefined;
    this.panelDisposable = undefined;
  }

  open(agent) {
    const name = displayText(agent && agent.name, "Détail de l’agent");

    if (!this.panel) {
      this.panel = this.vscode.window.createWebviewPanel(
        "agentWorld.agentDetail",
        `Agent World — ${name}`,
        this.vscode.ViewColumn.One,
        {
          enableScripts: false,
          retainContextWhenHidden: false,
          localResourceRoots: [],
        },
      );
      this.panelDisposable = this.panel.onDidDispose(() => {
        this.panel = undefined;
        this.panelDisposable = undefined;
      });
    } else {
      this.panel.title = `Agent World — ${name}`;
      this.panel.reveal(this.vscode.ViewColumn.One);
    }

    this.panel.webview.html = renderAgentDetailHtml({ agent });
  }

  dispose() {
    const panel = this.panel;
    this.panel = undefined;
    if (panel) {
      panel.dispose();
    }
    if (this.panelDisposable) {
      this.panelDisposable.dispose();
      this.panelDisposable = undefined;
    }
  }
}

function displayText(value, fallback) {
  if (value === undefined || value === null || String(value).trim() === "") {
    return fallback;
  }
  return String(value).trim().slice(0, 60);
}

function errorMessage(error) {
  return error instanceof Error ? error.message : String(error || "Erreur inconnue");
}

module.exports = {
  AgentDetailPanel,
  DashboardPanel,
};
