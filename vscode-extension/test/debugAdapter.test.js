"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const {
  AgentWorldDebugAdapter,
  AgentWorldDebugConfigurationProvider,
  PHASES,
  evaluateExpression,
  sanitizeForDebug,
  startAgentDebugging,
} = require("../src/debugAdapter");

class FakeEventEmitter {
  constructor() {
    this.listeners = [];
    this.event = (listener) => {
      this.listeners.push(listener);
      return { dispose: () => this.listeners.splice(this.listeners.indexOf(listener), 1) };
    };
  }

  fire(value) {
    for (const listener of [...this.listeners]) {
      listener(value);
    }
  }

  dispose() {
    this.listeners = [];
  }
}

test("le provider complète une configuration launch avec un agent choisi", async () => {
  const calls = { quickPick: 0, errors: [] };
  const agent = { id: 7, name: "Analyse", model: "mistral", is_active: true };
  const vscode = createVscode({
    showQuickPick: async (items) => {
      calls.quickPick += 1;
      return items[0];
    },
    showErrorMessage: async (message) => calls.errors.push(message),
  });
  const provider = new AgentWorldDebugConfigurationProvider(vscode, () => ({
    getAgents: async () => [agent],
  }));

  const configuration = await provider.resolveDebugConfiguration(undefined, {
    input: "bonjour",
  });

  assert.equal(configuration.type, "agent-world");
  assert.equal(configuration.request, "launch");
  assert.equal(configuration.agentId, 7);
  assert.equal(configuration.stopOnEntry, true);
  assert.equal(calls.quickPick, 1);
  assert.deepEqual(calls.errors, []);
});

test("le provider refuse le debug dans un workspace non approuvé", async () => {
  const errors = [];
  const vscode = createVscode({
    isTrusted: false,
    showErrorMessage: async (message) => errors.push(message),
  });
  const provider = new AgentWorldDebugConfigurationProvider(vscode, () => {
    throw new Error("le client ne doit pas être créé");
  });

  const configuration = await provider.resolveDebugConfiguration(undefined, {});

  assert.equal(configuration, undefined);
  assert.match(errors[0], /non approuvé/);
});

test("la commande de debug transmet l’agent et l’entrée à VS Code", async () => {
  let debugConfiguration;
  const vscode = createVscode({
    showInputBox: async () => "question",
    startDebugging: async (_folder, configuration) => {
      debugConfiguration = configuration;
      return true;
    },
  });

  const started = await startAgentDebugging(
    vscode,
    () => ({ getAgents: async () => [] }),
    { id: 4, name: "Recherche", is_active: true },
  );

  assert.equal(started, true);
  assert.deepEqual(debugConfiguration, {
    type: "agent-world",
    request: "launch",
    name: "Déboguer Recherche",
    agentId: 4,
    input: "question",
    stopOnEntry: true,
  });
});

test("la commande de debug refuse une entrée vide", async () => {
  const errors = [];
  let starts = 0;
  const vscode = createVscode({
    showInputBox: async () => "   ",
    showErrorMessage: async (message) => errors.push(message),
    startDebugging: async () => {
      starts += 1;
      return true;
    },
  });

  const started = await startAgentDebugging(
    vscode,
    () => ({ getAgents: async () => [] }),
    { id: 4, name: "Recherche", is_active: true },
  );

  assert.equal(started, false);
  assert.equal(starts, 0);
  assert.match(errors[0], /ne peut pas être vide/);
});

test("l’adaptateur vérifie les breakpoints et expose les variables", async () => {
  const agent = {
    id: 3,
    name: "Démo",
    model: "mistral",
    configuration: { temperature: 0.2, api_key: "très-secret" },
  };
  const { adapter, messages } = createAdapter({ agent });

  await request(adapter, 1, "initialize");
  await request(adapter, 2, "launch", { agentId: 3, input: "hello" });
  await request(adapter, 3, "setBreakpoints", {
    breakpoints: [{ line: 2 }, { line: 99 }],
  });
  await request(adapter, 4, "configurationDone");
  await request(adapter, 5, "stackTrace");
  await request(adapter, 6, "scopes");

  const breakpointResponse = response(messages, 3);
  assert.ok(event(messages, "initialized"));
  assert.equal(response(messages, 2).success, true);
  assert.equal(breakpointResponse.body.breakpoints[0].verified, true);
  assert.equal(breakpointResponse.body.breakpoints[1].verified, false);
  assert.equal(event(messages, "stopped").body.reason, "entry");
  assert.equal(response(messages, 5).body.stackFrames[0].line, 1);

  const [agentScope] = response(messages, 6).body.scopes;
  await request(adapter, 7, "variables", {
    variablesReference: agentScope.variablesReference,
  });
  const agentVariables = response(messages, 7).body.variables;
  const configuration = agentVariables.find((variable) => variable.name === "configuration");
  assert.ok(configuration.variablesReference > 0);

  await request(adapter, 8, "variables", {
    variablesReference: configuration.variablesReference,
  });
  const configurationVariables = response(messages, 8).body.variables;
  assert.equal(
    configurationVariables.find((variable) => variable.name === "api_key").value,
    "[redacted]",
  );
});

test("continue exécute l’agent, s’arrête sur le résultat puis termine", async () => {
  const completed = [];
  const execution = {
    execution_id: 12,
    agent_id: 3,
    status: "completed",
    output: { result: "ok" },
  };
  const { adapter, messages, calls } = createAdapter({
    execution,
    notifications: {
      async notifyTaskCompleted(agent, result) {
        completed.push({ agent, result });
      },
    },
  });

  await request(adapter, 1, "launch", { agentId: 3, input: "hello" });
  await request(adapter, 2, "setBreakpoints", { breakpoints: [{ line: 4 }] });
  await request(adapter, 3, "configurationDone");
  await request(adapter, 4, "continue");

  assert.deepEqual(calls.runAgent, [[3, "hello"]]);
  assert.equal(lastEvent(messages, "stopped").body.reason, "breakpoint");
  await request(adapter, 5, "stackTrace");
  assert.equal(response(messages, 5).body.stackFrames[0].line, 4);

  await request(adapter, 6, "continue");

  assert.equal(lastEvent(messages, "terminated").event, "terminated");
  assert.equal(completed.length, 1);
  assert.deepEqual(completed[0].result, execution);
});

test("next parcourt les cinq phases du cycle de debug", async () => {
  const { adapter, messages } = createAdapter();
  await request(adapter, 1, "launch", { agentId: 3, input: "" });
  await request(adapter, 2, "configurationDone");

  for (let index = 2; index <= PHASES.length; index += 1) {
    await request(adapter, index + 1, "next");
    await request(adapter, index + 10, "stackTrace");
    assert.equal(response(messages, index + 10).body.stackFrames[0].line, index);
  }
  await request(adapter, 30, "continue");
  assert.ok(lastEvent(messages, "terminated"));
});

test("la terminaison DAP n’attend pas la fermeture de la notification", async () => {
  let notificationStarted = false;
  const neverDismissed = new Promise(() => undefined);
  const { adapter, messages } = createAdapter({
    notifications: {
      notifyTaskCompleted() {
        notificationStarted = true;
        return neverDismissed;
      },
    },
  });
  await request(adapter, 1, "launch", { agentId: 3, input: "hello" });
  await request(adapter, 2, "configurationDone");

  await request(adapter, 3, "continue");

  assert.equal(notificationStarted, true);
  assert.ok(lastEvent(messages, "terminated"));
});

test("un résultat tardif après disconnect est ignoré", async () => {
  const pendingExecution = deferred();
  let executionStarted;
  const started = new Promise((resolve) => {
    executionStarted = resolve;
  });
  const completed = [];
  const failed = [];
  const vscode = createVscode();
  const adapter = new AgentWorldDebugAdapter(
    vscode,
    () => ({
      getAgent: async () => ({ id: 3, name: "Démo", is_active: true }),
      runAgent: async () => {
        executionStarted();
        return pendingExecution.promise;
      },
    }),
    {
      notifications: {
        async notifyTaskCompleted(...args) {
          completed.push(args);
        },
        async notifyTaskFailed(...args) {
          failed.push(args);
        },
      },
    },
  );
  const messages = [];
  adapter.onDidSendMessage((message) => messages.push(message));
  await request(adapter, 1, "launch", { agentId: 3, input: "hello" });
  await request(adapter, 2, "setBreakpoints", { breakpoints: [{ line: 4 }] });
  await request(adapter, 3, "configurationDone");
  const stoppedBeforeRun = messages.filter(
    (message) => message.type === "event" && message.event === "stopped",
  ).length;

  const continuing = adapter.dispatchRequest({
    type: "request",
    seq: 4,
    command: "continue",
  });
  await started;
  await request(adapter, 5, "disconnect");
  pendingExecution.resolve({ execution_id: 44, status: "completed" });
  await continuing;

  const terminatedIndex = messages.findIndex(
    (message) => message.type === "event" && message.event === "terminated",
  );
  assert.ok(terminatedIndex >= 0);
  assert.equal(
    messages.filter(
      (message) => message.type === "event" && message.event === "stopped",
    ).length,
    stoppedBeforeRun,
  );
  assert.equal(
    messages.slice(terminatedIndex + 1).some((message) => message.type === "event"),
    false,
  );
  assert.deepEqual(completed, []);
  assert.deepEqual(failed, []);
  assert.equal(adapter.execution, undefined);
});

test("une exécution échouée produit une notification d’échec uniquement", async () => {
  const completed = [];
  const failed = [];
  const { adapter, messages } = createAdapter({
    runError: new Error("Erreur fournisseur"),
    notifications: {
      async notifyTaskCompleted(...args) {
        completed.push(args);
      },
      async notifyTaskFailed(...args) {
        failed.push(args);
      },
    },
  });
  await request(adapter, 1, "launch", { agentId: 3, input: "hello" });
  await request(adapter, 2, "configurationDone");

  await request(adapter, 3, "continue");
  await Promise.resolve();

  assert.ok(lastEvent(messages, "terminated"));
  assert.equal(completed.length, 0);
  assert.equal(failed.length, 1);
  assert.equal(failed[0][0].id, 3);
  assert.match(failed[0][1], /Erreur fournisseur/);
  assert.equal(failed[0][2].status, "failed");
  assert.ok(failed[0][2].failure_id);
});

test("les expressions sont limitées à des chemins de variables sûrs", () => {
  assert.equal(
    evaluateExpression("agent.configuration.temperature", {
      agent: { configuration: { temperature: 0.4 } },
    }),
    0.4,
  );
  assert.throws(
    () => evaluateExpression("agent.constructor.constructor", { agent: {} }),
    /Variable inconnue/,
  );
  assert.throws(() => evaluateExpression("agent[\"name\"]", { agent: {} }), /chemins/);
});

test("les secrets imbriqués sont masqués sans modifier l’objet source", () => {
  const source = {
    token: "secret",
    nested: { password: "secret", visible: true },
  };

  const sanitized = sanitizeForDebug(source);

  assert.deepEqual(sanitized, {
    token: "[redacted]",
    nested: { password: "[redacted]", visible: true },
  });
  assert.equal(source.token, "secret");
});

function createAdapter({
  agent = { id: 3, name: "Démo", is_active: true, configuration: {} },
  execution = { execution_id: 1, status: "completed", output: {} },
  notifications,
  runError,
} = {}) {
  const calls = { runAgent: [] };
  const vscode = createVscode();
  const adapter = new AgentWorldDebugAdapter(
    vscode,
    () => ({
      getAgent: async () => agent,
      runAgent: async (agentId, input) => {
        calls.runAgent.push([agentId, input]);
        if (runError) {
          throw runError;
        }
        return execution;
      },
    }),
    { notifications },
  );
  const messages = [];
  adapter.onDidSendMessage((message) => messages.push(message));
  return { adapter, messages, calls };
}

function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

async function request(adapter, seq, command, args) {
  await adapter.dispatchRequest({
    type: "request",
    seq,
    command,
    arguments: args,
  });
}

function response(messages, requestSeq) {
  return messages.find(
    (message) => message.type === "response" && message.request_seq === requestSeq,
  );
}

function event(messages, name) {
  return messages.find((message) => message.type === "event" && message.event === name);
}

function lastEvent(messages, name) {
  return [...messages]
    .reverse()
    .find((message) => message.type === "event" && message.event === name);
}

function createVscode({
  isTrusted = true,
  showQuickPick = async () => undefined,
  showInputBox = async () => "",
  showErrorMessage = async () => undefined,
  showInformationMessage = async () => undefined,
  startDebugging = async () => true,
} = {}) {
  return {
    EventEmitter: FakeEventEmitter,
    workspace: { isTrusted },
    window: {
      showQuickPick,
      showInputBox,
      showErrorMessage,
      showInformationMessage,
    },
    debug: { startDebugging },
  };
}
