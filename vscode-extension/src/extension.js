"use strict";

const vscode = require("vscode");

const {
  AgentWorldApiClient,
  DEFAULT_BASE_URL,
  DEFAULT_TIMEOUT_MS,
} = require("./apiClient");
const { AgentTreeProvider } = require("./agentTreeProvider");
const { openGeneratedFile } = require("./fileCommands");
const { AgentDetailPanel, DashboardPanel } = require("./panels");

function activate(context) {
  const getClient = () => {
    const configuration = vscode.workspace.getConfiguration("agentWorld");
    return new AgentWorldApiClient({
      baseUrl: configuration.get("apiUrl", DEFAULT_BASE_URL),
      timeoutMs: configuration.get("requestTimeoutMs", DEFAULT_TIMEOUT_MS),
    });
  };

  const treeProvider = new AgentTreeProvider(vscode, getClient);
  const dashboardPanel = new DashboardPanel(vscode, getClient);
  const detailPanel = new AgentDetailPanel(vscode);

  const refresh = async () => {
    await Promise.all([treeProvider.refresh(), dashboardPanel.refreshIfVisible()]);
  };

  context.subscriptions.push(
    treeProvider,
    dashboardPanel,
    detailPanel,
    vscode.window.registerTreeDataProvider("agentWorld.agentsView", treeProvider),
    vscode.commands.registerCommand("agentWorld.openDashboard", () =>
      dashboardPanel.open(),
    ),
    vscode.commands.registerCommand("agentWorld.refreshAgents", refresh),
    vscode.commands.registerCommand("agentWorld.openAgentDetail", (agent) =>
      detailPanel.open(agent),
    ),
    vscode.commands.registerCommand("agentWorld.openGeneratedFile", (candidate) =>
      openGeneratedFile(vscode, candidate),
    ),
    vscode.workspace.onDidChangeConfiguration((event) => {
      if (
        event.affectsConfiguration("agentWorld.apiUrl") ||
        event.affectsConfiguration("agentWorld.requestTimeoutMs")
      ) {
        void refresh();
      }
    }),
  );

  void treeProvider.refresh();
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
