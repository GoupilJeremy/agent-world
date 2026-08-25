"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const { RunAgentCommand } = require("../src/runAgentCommand");

test("un agent et une consigne fournis sont exécutés puis notifiés", async () => {
  const fixture = createFixture();
  const command = new RunAgentCommand(fixture.vscode, {
    getClient: () => fixture.client,
    notificationService: fixture.notificationService,
  });
  const agent = { id: 8, name: "Direct" };

  const result = await command.execute(agent, "  Analyser ce fichier  ");

  assert.equal(result.status, "completed");
  assert.deepEqual(fixture.runs, [{ agentId: 8, input: "Analyser ce fichier" }]);
  assert.deepEqual(fixture.notifications, [
    { agent, execution: fixture.execution },
  ]);
  assert.equal(fixture.getAgentsCount, 0);
});

test("la palette et le champ de saisie complètent les arguments manquants", async () => {
  const agent = { id: 2, name: "Choisi", model: "mistral" };
  const fixture = createFixture({ agents: [agent], selectedAgentId: 2, input: "Résumer" });
  const command = new RunAgentCommand(fixture.vscode, {
    getClient: () => fixture.client,
    notificationService: fixture.notificationService,
  });

  const result = await command.execute();

  assert.equal(result.status, "completed");
  assert.equal(fixture.getAgentsCount, 1);
  assert.deepEqual(fixture.runs, [{ agentId: 2, input: "Résumer" }]);
  assert.equal(fixture.pickerItems[0].agent, agent);
});

test("annuler la sélection d’agent arrête le flux avant l’exécution", async () => {
  const fixture = createFixture({
    agents: [{ id: 4, name: "Annulé" }],
    selectedAgentId: undefined,
  });
  const command = new RunAgentCommand(fixture.vscode, {
    getClient: () => fixture.client,
    notificationService: fixture.notificationService,
  });

  const result = await command.execute();

  assert.equal(result.status, "cancelled");
  assert.deepEqual(fixture.runs, []);
  assert.deepEqual(fixture.notifications, []);
});

test("annuler la saisie arrête le flux avant l’exécution", async () => {
  const fixture = createFixture({ input: undefined });
  const command = new RunAgentCommand(fixture.vscode, {
    getClient: () => fixture.client,
    notificationService: fixture.notificationService,
  });

  const result = await command.execute({ id: 6, name: "Agent" });

  assert.equal(result.status, "cancelled");
  assert.deepEqual(fixture.runs, []);
});

test("une erreur API est présentée et ne déclenche aucune notification", async () => {
  const fixture = createFixture({ runError: new Error("API indisponible") });
  const command = new RunAgentCommand(fixture.vscode, {
    getClient: () => fixture.client,
    notificationService: fixture.notificationService,
  });

  const result = await command.execute({ id: 9, name: "Erreur" }, "Tester");

  assert.equal(result.status, "error");
  assert.deepEqual(fixture.notifications, []);
  assert.match(fixture.errors[0], /API indisponible/);
});

test("une exécution encore en cours n’est pas annoncée comme terminée", async () => {
  const fixture = createFixture({
    execution: { execution_id: 72, agent_id: 9, status: "running" },
  });
  const command = new RunAgentCommand(fixture.vscode, {
    getClient: () => fixture.client,
    notificationService: fixture.notificationService,
  });

  const result = await command.execute({ id: 9, name: "En cours" }, "Tester");

  assert.equal(result.status, "error");
  assert.deepEqual(fixture.notifications, []);
  assert.match(fixture.errors[0], /n’est pas terminée/);
});

test("une liste vide est signalée sans demander de consigne", async () => {
  const fixture = createFixture({ agents: [] });
  const command = new RunAgentCommand(fixture.vscode, {
    getClient: () => fixture.client,
    notificationService: fixture.notificationService,
  });

  const result = await command.execute();

  assert.equal(result.status, "cancelled");
  assert.match(fixture.informationMessages[0], /Aucun agent/);
  assert.equal(fixture.inputRequests, 0);
});

function createFixture(options = {}) {
  const agents = options.agents || [];
  const execution = options.execution || {
    execution_id: 71,
    agent_id: 8,
    status: "completed",
  };
  const runs = [];
  const notifications = [];
  const errors = [];
  const informationMessages = [];
  let getAgentsCount = 0;
  let pickerItems = [];
  let inputRequests = 0;

  const fixture = {
    execution,
    runs,
    notifications,
    errors,
    informationMessages,
    client: {
      async getAgents() {
        getAgentsCount += 1;
        return agents;
      },
      async runAgent(agentId, input) {
        runs.push({ agentId, input });
        if (options.runError) {
          throw options.runError;
        }
        if (!options.execution) {
          execution.agent_id = agentId;
        }
        return execution;
      },
    },
    notificationService: {
      async notifyTaskCompleted(agent, completedExecution) {
        notifications.push({ agent, execution: completedExecution });
        return { status: "notified" };
      },
    },
    vscode: {
      window: {
        async showQuickPick(items) {
          pickerItems = items;
          return items.find((item) => item.agent.id === options.selectedAgentId);
        },
        async showInputBox() {
          inputRequests += 1;
          return options.input;
        },
        async showInformationMessage(message) {
          informationMessages.push(message);
        },
        async showErrorMessage(message) {
          errors.push(message);
        },
      },
    },
  };

  Object.defineProperties(fixture, {
    getAgentsCount: { get: () => getAgentsCount },
    pickerItems: { get: () => pickerItems },
    inputRequests: { get: () => inputRequests },
  });
  return fixture;
}
