"use strict";

const vscode = require("vscode");

const {
  AgentWorldApiClient,
  DEFAULT_BASE_URL,
  DEFAULT_EXECUTION_TIMEOUT_MS,
  DEFAULT_TIMEOUT_MS,
} = require("./apiClient");
const { AgentTreeProvider } = require("./agentTreeProvider");
const {
  AgentWorldDebugAdapterFactory,
  AgentWorldDebugConfigurationProvider,
  DEBUG_TYPE,
  startAgentDebugging,
} = require("./debugAdapter");
const { openGeneratedFile } = require("./fileCommands");
const { withSelectedAgent } = require("./gitCommand");
const { GitIntegration, repositoryLabel } = require("./gitIntegration");
const { NotificationService } = require("./notificationService");
const { AgentDetailPanel, DashboardPanel } = require("./panels");
const { RunAgentCommand, unwrapAgent } = require("./runAgentCommand");
const { VscodeCommandService } = require("./vscodeCommandService");

function activate(context) {
  const getClient = () => {
    const configuration = vscode.workspace.getConfiguration("agentWorld");
    return new AgentWorldApiClient({
      baseUrl: configuration.get("apiUrl", DEFAULT_BASE_URL),
      timeoutMs: configuration.get("requestTimeoutMs", DEFAULT_TIMEOUT_MS),
      executionTimeoutMs: configuration.get(
        "executionTimeoutMs",
        DEFAULT_EXECUTION_TIMEOUT_MS,
      ),
    });
  };

  const treeProvider = new AgentTreeProvider(vscode, getClient);
  const dashboardPanel = new DashboardPanel(vscode, getClient);
  const detailPanel = new AgentDetailPanel(vscode);
  const notificationService = new NotificationService(vscode, {
    state: context.globalState,
    scope: () =>
      vscode.workspace
        .getConfiguration("agentWorld")
        .get("apiUrl", DEFAULT_BASE_URL),
  });
  const runAgentCommand = new RunAgentCommand(vscode, {
    getClient,
    notificationService,
  });
  const vscodeCommandService = new VscodeCommandService(vscode);
  const gitIntegration = new GitIntegration(vscode, context.workspaceState);
  const debugConfigurationProvider = new AgentWorldDebugConfigurationProvider(
    vscode,
    getClient,
  );
  const debugAdapterFactory = new AgentWorldDebugAdapterFactory(
    vscode,
    getClient,
    notificationService,
  );

  const refresh = async () => {
    await Promise.all([treeProvider.refresh(), dashboardPanel.refreshIfVisible()]);
  };

  context.subscriptions.push(
    treeProvider,
    dashboardPanel,
    detailPanel,
    gitIntegration,
    vscode.window.registerTreeDataProvider("agentWorld.agentsView", treeProvider),
    vscode.commands.registerCommand("agentWorld.openDashboard", () =>
      dashboardPanel.open(),
    ),
    vscode.commands.registerCommand("agentWorld.refreshAgents", refresh),
    vscode.commands.registerCommand("agentWorld.openAgentDetail", (candidate) =>
      detailPanel.open(unwrapAgent(candidate)),
    ),
    vscode.commands.registerCommand("agentWorld.openGeneratedFile", (candidate) =>
      openGeneratedFile(vscode, candidate),
    ),
    vscode.commands.registerCommand(
      "agentWorld.executeVscodeCommand",
      (actionId) =>
        typeof actionId === "string"
          ? vscodeCommandService.execute(actionId)
          : vscodeCommandService.pickAndExecute(),
    ),
    vscode.commands.registerCommand("agentWorld.runAgent", (candidate, input) =>
      runAgentCommand.execute(candidate, input),
    ),
    vscode.commands.registerCommand("agentWorld.debugAgent", (candidate) =>
      startAgentDebugging(vscode, getClient, unwrapAgent(candidate)),
    ),
    vscode.commands.registerCommand(
      "agentWorld.linkAgentRepository",
      (candidate) =>
        withSelectedAgent(vscode, getClient, candidate, (agent) =>
          gitIntegration.linkAgentToRepository(agent),
        ),
    ),
    vscode.commands.registerCommand(
      "agentWorld.commitAgentChanges",
      (candidate) =>
        withSelectedAgent(vscode, getClient, candidate, (agent) =>
          gitIntegration.stageAndCommit(agent),
        ),
    ),
    vscode.commands.registerCommand(
      "agentWorld.pushAgentChanges",
      (candidate) =>
        withSelectedAgent(vscode, getClient, candidate, (agent) =>
          gitIntegration.push(agent),
        ),
    ),
    vscode.debug.registerDebugConfigurationProvider(
      DEBUG_TYPE,
      debugConfigurationProvider,
    ),
    vscode.debug.registerDebugAdapterDescriptorFactory(
      DEBUG_TYPE,
      debugAdapterFactory,
    ),
    gitIntegration.onDidChangeRepository(({ repository, summary }) => {
      if (!summary.hasChanges) {
        return;
      }
      const label =
        summary.total === 1 ? "1 changement Git" : `${summary.total} changements Git`;
      vscode.window.setStatusBarMessage(
        `$(git-commit) Agent World — ${repositoryLabel(repository)} : ${label}`,
        3000,
      );
    }),
    vscode.workspace.onDidChangeConfiguration((event) => {
      if (
        event.affectsConfiguration("agentWorld.apiUrl") ||
        event.affectsConfiguration("agentWorld.requestTimeoutMs") ||
        event.affectsConfiguration("agentWorld.executionTimeoutMs")
      ) {
        void refresh();
      }
    }),
  );

  void treeProvider.refresh();
  void gitIntegration.initialize();
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
  withSelectedAgent,
};
