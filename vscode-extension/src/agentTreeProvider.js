"use strict";

class AgentTreeProvider {
  constructor(vscode, getClient) {
    this.vscode = vscode;
    this.getClient = getClient;
    this.requestVersion = 0;
    this.items = [createState("loading")];
    this.changeEmitter = new vscode.EventEmitter();
    this.onDidChangeTreeData = this.changeEmitter.event;
  }

  getTreeItem(element) {
    const { TreeItem, TreeItemCollapsibleState, ThemeIcon } = this.vscode;

    if (element.kind === "agent") {
      const item = new TreeItem(agentLabel(element.agent), TreeItemCollapsibleState.None);
      item.description = agentDescription(element.agent);
      item.tooltip = agentTooltip(element.agent);
      item.contextValue = "agentWorld.agent";
      item.iconPath = new ThemeIcon("hubot");
      item.command = {
        command: "agentWorld.openAgentDetail",
        title: "Afficher le détail de l’agent",
        arguments: [element.agent],
      };
      return item;
    }

    const item = new TreeItem(element.label, TreeItemCollapsibleState.None);
    item.contextValue = `agentWorld.${element.state}`;
    item.tooltip = element.tooltip;

    if (element.state === "loading") {
      item.iconPath = new ThemeIcon("loading~spin");
    } else if (element.state === "empty") {
      item.iconPath = new ThemeIcon("info");
    } else {
      item.iconPath = new ThemeIcon("error");
      item.description = "Cliquer pour réessayer";
      item.command = {
        command: "agentWorld.refreshAgents",
        title: "Réessayer",
      };
    }

    return item;
  }

  getChildren(element) {
    if (element) {
      return [];
    }
    return this.items;
  }

  async refresh() {
    const currentRequest = ++this.requestVersion;
    this.items = [createState("loading")];
    this.changeEmitter.fire(undefined);

    try {
      const agents = await this.getClient().getAgents();
      if (currentRequest !== this.requestVersion) {
        return;
      }

      const validAgents = agents.filter(
        (agent) => agent && typeof agent === "object" && !Array.isArray(agent),
      );
      this.items = validAgents.length
        ? validAgents.map((agent) => ({ kind: "agent", agent }))
        : [createState("empty")];
    } catch (error) {
      if (currentRequest !== this.requestVersion) {
        return;
      }
      this.items = [createState("error", errorMessage(error))];
    }

    this.changeEmitter.fire(undefined);
  }

  dispose() {
    this.requestVersion += 1;
    this.changeEmitter.dispose();
  }
}

function createState(state, detail = "") {
  if (state === "empty") {
    return {
      kind: "state",
      state,
      label: "Aucun agent disponible",
      tooltip: "L’API Agent World n’a retourné aucun agent.",
    };
  }

  if (state === "error") {
    return {
      kind: "state",
      state,
      label: "Impossible de charger les agents",
      tooltip: detail,
    };
  }

  return {
    kind: "state",
    state: "loading",
    label: "Chargement des agents…",
    tooltip: "Connexion à l’API Agent World.",
  };
}

function agentLabel(agent) {
  const name = displayText(agent.name);
  if (name) {
    return name;
  }
  const id = displayText(agent.id);
  return id ? `Agent #${id}` : "Agent sans nom";
}

function agentDescription(agent) {
  const model = displayText(agent.model);
  if (model) {
    return model;
  }
  return agent.is_active === false ? "inactif" : "";
}

function agentTooltip(agent) {
  const parts = [agentLabel(agent)];
  const model = displayText(agent.model);
  const description = displayText(agent.description);
  if (model) {
    parts.push(`Modèle : ${model}`);
  }
  if (description) {
    parts.push(description);
  }
  return parts.join("\n");
}

function displayText(value) {
  if (value === undefined || value === null) {
    return "";
  }
  return String(value).trim();
}

function errorMessage(error) {
  return error instanceof Error ? error.message : String(error || "Erreur inconnue");
}

module.exports = {
  AgentTreeProvider,
  agentDescription,
  agentLabel,
  createState,
  errorMessage,
};
