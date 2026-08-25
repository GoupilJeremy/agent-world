"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");

const extensionRoot = path.resolve(__dirname, "..");
const manifest = JSON.parse(
  fs.readFileSync(path.join(extensionRoot, "package.json"), "utf8"),
);

test("le manifeste déclare un point d’entrée et un moteur VS Code valides", () => {
  assert.equal(manifest.main, "./src/extension.js");
  assert.match(manifest.engines.vscode, /^\^\d+\.\d+\.\d+$/);
  assert.equal(
    fs.existsSync(path.join(extensionRoot, manifest.main)),
    true,
    "le point d’entrée doit exister",
  );
});

test("le manifeste contribue l’Activity Bar et la vue Agents", () => {
  const [container] = manifest.contributes.viewsContainers.activitybar;
  const [view] = manifest.contributes.views.agentWorld;

  assert.equal(container.id, "agentWorld");
  assert.equal(container.icon, "media/agent-world.svg");
  assert.equal(view.id, "agentWorld.agentsView");
  assert.equal(
    fs.existsSync(path.join(extensionRoot, container.icon)),
    true,
    "l’icône de l’Activity Bar doit exister",
  );
});

test("le manifeste déclare les commandes et le réglage API contractuels", () => {
  const commands = new Set(
    manifest.contributes.commands.map((contribution) => contribution.command),
  );

  assert.deepEqual(
    commands,
    new Set([
      "agentWorld.openDashboard",
      "agentWorld.refreshAgents",
      "agentWorld.openAgentDetail",
      "agentWorld.openGeneratedFile",
      "agentWorld.executeVscodeCommand",
      "agentWorld.runAgent",
      "agentWorld.debugAgent",
      "agentWorld.linkAgentRepository",
      "agentWorld.commitAgentChanges",
      "agentWorld.pushAgentChanges",
    ]),
  );
  const apiConfiguration =
    manifest.contributes.configuration.properties["agentWorld.apiUrl"];
  assert.equal(apiConfiguration.default, "http://127.0.0.1:5000");
  assert.equal(apiConfiguration.scope, "machine");
  assert.deepEqual(apiConfiguration.tags, ["usesOnlineServices"]);
  assert.equal(
    manifest.contributes.configuration.properties["agentWorld.executionTimeoutMs"]
      .default,
    120000,
  );
  assert.deepEqual(
    manifest.contributes.configuration.properties["agentWorld.openFile.location"].enum,
    ["active", "beside"],
  );
  assert.equal(
    manifest.contributes.configuration.properties["agentWorld.openFile.location"].default,
    "active",
  );
  for (const contribution of manifest.contributes.commands) {
    assert.doesNotMatch(contribution.title, /^Agent World\s*:/);
  }
  assert.equal(manifest.capabilities.untrustedWorkspaces.supported, "limited");
  assert.match(
    manifest.capabilities.untrustedWorkspaces.description,
    /ouverture programmatique/,
  );
});

test("le manifeste déclare toutes les intégrations de l’EPIC 2", () => {
  const activationEvents = new Set(manifest.activationEvents);
  for (const command of [
    "executeVscodeCommand",
    "runAgent",
    "debugAgent",
    "linkAgentRepository",
    "commitAgentChanges",
    "pushAgentChanges",
  ]) {
    assert.equal(
      activationEvents.has(`onCommand:agentWorld.${command}`),
      true,
      `activation manquante pour ${command}`,
    );
  }
  assert.equal(activationEvents.has("onDebugResolve:agent-world"), true);
  assert.equal(activationEvents.has("onDebugInitialConfigurations"), true);

  assert.deepEqual(manifest.contributes.breakpoints, [{ language: "plaintext" }]);

  const paletteConditions = Object.fromEntries(
    manifest.contributes.menus.commandPalette.map((item) => [
      item.command,
      item.when,
    ]),
  );
  for (const command of [
    "agentWorld.openGeneratedFile",
    "agentWorld.executeVscodeCommand",
    "agentWorld.debugAgent",
    "agentWorld.linkAgentRepository",
    "agentWorld.commitAgentChanges",
    "agentWorld.pushAgentChanges",
  ]) {
    assert.equal(paletteConditions[command], "isWorkspaceTrusted");
  }
  const titleConditions = Object.fromEntries(
    manifest.contributes.menus["view/title"].map((item) => [
      item.command,
      item.when,
    ]),
  );
  assert.match(
    titleConditions["agentWorld.openGeneratedFile"],
    /isWorkspaceTrusted/,
  );

  const [debuggerContribution] = manifest.contributes.debuggers;
  assert.equal(debuggerContribution.type, "agent-world");
  assert.equal(debuggerContribution.label, "Agent World");
  assert.deepEqual(
    debuggerContribution.configurationAttributes.launch.required,
    ["agentId"],
  );
  assert.equal(
    debuggerContribution.configurationAttributes.launch.properties.stopOnEntry.default,
    true,
  );

  const contextCommands = new Set(
    manifest.contributes.menus["view/item/context"].map((item) => item.command),
  );
  for (const command of [
    "agentWorld.runAgent",
    "agentWorld.debugAgent",
    "agentWorld.linkAgentRepository",
    "agentWorld.commitAgentChanges",
    "agentWorld.pushAgentChanges",
  ]) {
    assert.equal(contextCommands.has(command), true);
  }
});
