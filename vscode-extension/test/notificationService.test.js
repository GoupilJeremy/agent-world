"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const {
  COMPLETION_STORAGE_KEY,
  NotificationService,
  VIEW_AGENT_ACTION,
  completionKey,
} = require("../src/notificationService");

test("un clic sur la notification ouvre le détail de l’agent", async () => {
  const openedAgents = [];
  const fixture = createFixture({ selectedAction: VIEW_AGENT_ACTION });
  const service = new NotificationService(fixture.vscode, {
    openAgentDetail: async (agent) => openedAgents.push(agent),
  });
  const agent = { id: 7, name: "Analyse" };

  const result = await service.notifyTaskCompleted(agent, {
    execution_id: 42,
    status: "completed",
  });

  assert.equal(result.status, "opened");
  assert.deepEqual(openedAgents, [agent]);
  assert.match(fixture.informationMessages[0], /Analyse/);
});

test("sans callback, le clic utilise la commande de détail Agent World", async () => {
  const fixture = createFixture({ selectedAction: VIEW_AGENT_ACTION });
  const service = new NotificationService(fixture.vscode);
  const agent = { id: 12, name: "Navigation" };

  const result = await service.notifyTaskCompleted(agent, { id: 81 });

  assert.equal(result.status, "opened");
  assert.deepEqual(fixture.executedCommands, [
    { commandId: "agentWorld.openAgentDetail", agent },
  ]);
});

test("une exécution déjà notifiée est dédupliquée", async () => {
  const fixture = createFixture();
  const service = new NotificationService(fixture.vscode);
  const agent = { id: 3, name: "Résumé" };
  const execution = { execution_id: 11 };

  const first = await service.notifyTaskCompleted(agent, execution);
  const duplicate = await service.notifyTaskCompleted(agent, execution);

  assert.equal(first.status, "notified");
  assert.equal(duplicate.status, "duplicate");
  assert.equal(fixture.informationMessages.length, 1);
});

test("la déduplication sépare les exécutions de deux endpoints API", async () => {
  const values = new Map();
  const state = {
    get(key, fallback) {
      return values.has(key) ? values.get(key) : fallback;
    },
    async update(key, value) {
      values.set(key, value);
    },
  };
  const firstFixture = createFixture();
  const secondFixture = createFixture();
  const execution = { execution_id: 11, agent_id: 3 };
  const agent = { id: 3, name: "Résumé" };

  await new NotificationService(firstFixture.vscode, {
    state,
    scope: "http://server-a.invalid",
  }).notifyTaskCompleted(agent, execution);
  const result = await new NotificationService(secondFixture.vscode, {
    state,
    scope: "http://server-b.invalid",
  }).notifyTaskCompleted(agent, execution);

  assert.equal(result.status, "notified");
  assert.equal(firstFixture.informationMessages.length, 1);
  assert.equal(secondFixture.informationMessages.length, 1);
});

test("une erreur d'affichage ne consomme pas la clé de déduplication", async () => {
  let attempts = 0;
  const errors = [];
  const service = new NotificationService({
    window: {
      async showInformationMessage() {
        attempts += 1;
        if (attempts === 1) {
          throw new Error("UI indisponible");
        }
      },
      async showErrorMessage(message) {
        errors.push(message);
      },
    },
    commands: { executeCommand: async () => undefined },
  });
  const execution = { execution_id: 12, agent_id: 3 };

  const first = await service.notifyTaskCompleted({ id: 3 }, execution);
  const retry = await service.notifyTaskCompleted({ id: 3 }, execution);

  assert.equal(first.status, "error");
  assert.equal(retry.status, "notified");
  assert.equal(attempts, 2);
  assert.match(errors[0], /UI indisponible/);
});

test("la déduplication est restaurée depuis l’état persistant", async () => {
  const values = new Map();
  const state = {
    get(key, fallback) {
      return values.has(key) ? values.get(key) : fallback;
    },
    async update(key, value) {
      values.set(key, value);
    },
  };
  const agent = { id: 5, name: "Persistant" };
  const execution = { id: 99 };

  const firstFixture = createFixture();
  const firstService = new NotificationService(firstFixture.vscode, { state });
  await firstService.notifyTaskCompleted(agent, execution);

  const secondFixture = createFixture();
  const secondService = new NotificationService(secondFixture.vscode, { state });
  const result = await secondService.notifyTaskCompleted(agent, execution);

  assert.equal(result.status, "duplicate");
  assert.equal(secondFixture.informationMessages.length, 0);
  assert.deepEqual(values.get(COMPLETION_STORAGE_KEY), [completionKey(agent, execution)]);
});

test("la déduplication conserve une fenêtre bornée", async () => {
  const fixture = createFixture();
  const service = new NotificationService(fixture.vscode, { maxEntries: 2 });
  const agent = { id: 1, name: "Agent" };

  await service.notifyTaskCompleted(agent, { id: 1 });
  await service.notifyTaskCompleted(agent, { id: 2 });
  await service.notifyTaskCompleted(agent, { id: 3 });
  const result = await service.notifyTaskCompleted(agent, { id: 1 });

  assert.equal(result.status, "notified");
  assert.equal(fixture.informationMessages.length, 4);
});

test("une exécution sans identifiant produit une erreur explicite", async () => {
  const fixture = createFixture();
  const service = new NotificationService(fixture.vscode);

  const result = await service.notifyTaskCompleted({ id: 1 }, { status: "completed" });

  assert.equal(result.status, "error");
  assert.equal(fixture.informationMessages.length, 0);
  assert.match(fixture.errors[0], /identifiant d’exécution/);
});

test("une notification d’échec ouvre le détail de l’agent", async () => {
  const fixture = createFixture({ selectedErrorAction: VIEW_AGENT_ACTION });
  const service = new NotificationService(fixture.vscode);
  const agent = { id: 15, name: "Échec contrôlé" };

  const result = await service.notifyTaskFailed(
    agent,
    new Error("Fournisseur indisponible"),
    { execution_id: 91, agent_id: 15, status: "failed" },
  );

  assert.equal(result.status, "opened");
  assert.match(fixture.errors[0], /Échec contrôlé/);
  assert.match(fixture.errors[0], /Fournisseur indisponible/);
  assert.deepEqual(fixture.executedCommands, [
    { commandId: "agentWorld.openAgentDetail", agent },
  ]);
});

test("un échec sans identifiant reste notifiable et dédupliqué", async () => {
  const fixture = createFixture();
  const service = new NotificationService(fixture.vscode);
  const agent = { id: 16, name: "Sans identifiant" };

  const first = await service.notifyTaskFailed(agent, "Connexion interrompue");
  const duplicate = await service.notifyTaskFailed(agent, "Connexion interrompue");

  assert.equal(first.status, "notified");
  assert.equal(duplicate.status, "duplicate");
  assert.equal(fixture.errors.length, 1);
  assert.match(fixture.errors[0], /a échoué/);
});

function createFixture({
  selectedAction = undefined,
  selectedErrorAction = undefined,
} = {}) {
  const informationMessages = [];
  const errors = [];
  const executedCommands = [];
  return {
    informationMessages,
    errors,
    executedCommands,
    vscode: {
      window: {
        async showInformationMessage(message) {
          informationMessages.push(message);
          return selectedAction;
        },
        async showErrorMessage(message) {
          errors.push(message);
          return selectedErrorAction;
        },
      },
      commands: {
        async executeCommand(commandId, agent) {
          executedCommands.push({ commandId, agent });
        },
      },
    },
  };
}
