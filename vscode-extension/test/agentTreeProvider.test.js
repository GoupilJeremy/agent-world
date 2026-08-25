"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const { AgentTreeProvider } = require("../src/agentTreeProvider");

class FakeEventEmitter {
  constructor() {
    this.fireCount = 0;
    this.event = () => ({ dispose() {} });
  }

  fire() {
    this.fireCount += 1;
  }

  dispose() {}
}

class FakeTreeItem {
  constructor(label, collapsibleState) {
    this.label = label;
    this.collapsibleState = collapsibleState;
  }
}

class FakeThemeIcon {
  constructor(id) {
    this.id = id;
  }
}

const fakeVscode = {
  EventEmitter: FakeEventEmitter,
  TreeItem: FakeTreeItem,
  TreeItemCollapsibleState: { None: 0 },
  ThemeIcon: FakeThemeIcon,
};

test("la vue expose les agents et ouvre leur détail au clic", async () => {
  const provider = new AgentTreeProvider(fakeVscode, () => ({
    getAgents: async () => [
      { id: 7, name: "Analyse", model: "mistral-small", description: "Démo" },
    ],
  }));

  await provider.refresh();
  const [entry] = provider.getChildren();
  const item = provider.getTreeItem(entry);

  assert.equal(entry.kind, "agent");
  assert.equal(item.label, "Analyse");
  assert.equal(item.description, "mistral-small");
  assert.equal(item.contextValue, "agentWorld.agent");
  assert.equal(item.command.command, "agentWorld.openAgentDetail");
  assert.deepEqual(item.command.arguments, [entry.agent]);
});

test("la vue affiche explicitement un état vide", async () => {
  const provider = new AgentTreeProvider(fakeVscode, () => ({
    getAgents: async () => [],
  }));

  await provider.refresh();
  const [entry] = provider.getChildren();
  const item = provider.getTreeItem(entry);

  assert.equal(entry.state, "empty");
  assert.equal(item.label, "Aucun agent disponible");
  assert.equal(item.iconPath.id, "info");
});

test("la vue affiche une erreur actionnable sans propager le rejet", async () => {
  const provider = new AgentTreeProvider(fakeVscode, () => ({
    getAgents: async () => {
      throw new Error("API hors ligne");
    },
  }));

  await provider.refresh();
  const [entry] = provider.getChildren();
  const item = provider.getTreeItem(entry);

  assert.equal(entry.state, "error");
  assert.match(item.tooltip, /API hors ligne/);
  assert.equal(item.command.command, "agentWorld.refreshAgents");
});
