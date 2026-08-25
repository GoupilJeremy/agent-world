"use strict";

const DEBUG_TYPE = "agent-world";
const THREAD_ID = 1;
const SOURCE_REFERENCE = 1;
const PHASES = Object.freeze([
  { line: 1, name: "Chargement de l’agent" },
  { line: 2, name: "Validation de l’entrée" },
  { line: 3, name: "Appel de l’API Agent World" },
  { line: 4, name: "Inspection du résultat" },
  { line: 5, name: "Fin de l’exécution" },
]);
const SENSITIVE_KEY = /(api.?key|authorization|credential|password|secret|token)/i;

class AgentWorldDebugConfigurationProvider {
  constructor(vscode, getClient) {
    this.vscode = vscode;
    this.getClient = getClient;
  }

  provideDebugConfigurations() {
    return [
      {
        type: DEBUG_TYPE,
        request: "launch",
        name: "Déboguer un agent Agent World",
        agentId: "",
        input: "",
        stopOnEntry: true,
      },
    ];
  }

  async resolveDebugConfiguration(_folder, configuration) {
    if (this.vscode.workspace.isTrusted !== true) {
      await this.vscode.window.showErrorMessage(
        "Le débogage Agent World est désactivé dans un workspace non approuvé.",
      );
      return undefined;
    }

    const resolved = { ...configuration };
    resolved.type = DEBUG_TYPE;
    resolved.request = resolved.request || "launch";
    if (resolved.request !== "launch") {
      await this.vscode.window.showErrorMessage(
        "Agent World prend uniquement en charge les configurations de type launch.",
      );
      return undefined;
    }

    let agent;
    if (!hasValue(resolved.agentId) || isUnresolvedVariable(resolved.agentId)) {
      agent = await chooseAgent(this.vscode, this.getClient);
      if (!agent) {
        return undefined;
      }
      resolved.agentId = agent.id;
    } else {
      try {
        agent = await this.getClient().getAgent(resolved.agentId);
      } catch (error) {
        await this.vscode.window.showErrorMessage(
          `Impossible de préparer le débogage : ${errorMessage(error)}`,
        );
        return undefined;
      }
    }

    if (agent.is_active === false) {
      await this.vscode.window.showErrorMessage(
        `L’agent « ${agentLabel(agent)} » est inactif et ne peut pas être débogué.`,
      );
      return undefined;
    }

    if (typeof resolved.input !== "string" || resolved.input.trim() === "") {
      const input = await this.vscode.window.showInputBox({
        title: `Agent World — Déboguer ${agentLabel(agent)}`,
        prompt: "Entrée transmise à l’agent",
        ignoreFocusOut: true,
        validateInput: validateAgentInput,
      });
      if (input === undefined) {
        return undefined;
      }
      resolved.input = input.trim();
    }
    if (!resolved.input) {
      await this.vscode.window.showErrorMessage(
        "L’entrée de débogage ne peut pas être vide.",
      );
      return undefined;
    }

    resolved.name = resolved.name || `Déboguer ${agentLabel(agent)}`;
    resolved.stopOnEntry = resolved.stopOnEntry !== false;
    return resolved;
  }
}

class AgentWorldDebugAdapterFactory {
  constructor(vscode, getClient, notifications) {
    this.vscode = vscode;
    this.getClient = getClient;
    this.notifications = notifications;
  }

  createDebugAdapterDescriptor(session) {
    const adapter = new AgentWorldDebugAdapter(this.vscode, this.getClient, {
      configuration: session.configuration,
      notifications: this.notifications,
    });
    return new this.vscode.DebugAdapterInlineImplementation(adapter);
  }
}

class AgentWorldDebugAdapter {
  constructor(vscode, getClient, { configuration = {}, notifications } = {}) {
    this.vscode = vscode;
    this.getClient = getClient;
    this.configuration = { ...configuration };
    this.notifications = notifications;
    this.sequence = 1;
    this.currentLine = 1;
    this.breakpoints = new Set();
    this.agent = undefined;
    this.execution = undefined;
    this.executionPromise = undefined;
    this.executionError = undefined;
    this.terminated = false;
    this.configurationDone = false;
    this.started = false;
    this.pendingLaunchRequest = undefined;
    this.resumeQueue = Promise.resolve();
    this.variableContainers = new Map();
    this.nextVariableReference = 10;
    this.messageEmitter = new vscode.EventEmitter();
    this.onDidSendMessage = this.messageEmitter.event;
  }

  handleMessage(message) {
    if (!message || message.type !== "request") {
      return;
    }
    void this.dispatchRequest(message).catch((error) => {
      this.sendErrorResponse(message, error);
    });
  }

  async dispatchRequest(request) {
    switch (request.command) {
      case "initialize":
        this.sendResponse(request, {
          supportsConfigurationDoneRequest: true,
          supportsEvaluateForHovers: true,
          supportsLoadedSourcesRequest: true,
        });
        this.sendEvent("initialized");
        return;
      case "launch":
        await this.launch(request);
        return;
      case "setBreakpoints":
        this.setBreakpoints(request);
        return;
      case "configurationDone":
        this.configurationDone = true;
        this.sendResponse(request);
        await this.completeLaunchIfReady();
        return;
      case "threads":
        this.sendResponse(request, {
          threads: [{ id: THREAD_ID, name: "Agent World" }],
        });
        return;
      case "stackTrace":
        this.sendResponse(request, {
          stackFrames: [this.stackFrame()],
          totalFrames: 1,
        });
        return;
      case "scopes":
        this.sendResponse(request, { scopes: this.scopes() });
        return;
      case "variables":
        this.sendResponse(request, {
          variables: this.variables(request.arguments?.variablesReference),
        });
        return;
      case "evaluate":
        this.evaluate(request);
        return;
      case "source":
        this.sendResponse(request, {
          content: sourceContent(this.agent),
          mimeType: "text/plain",
        });
        return;
      case "loadedSources":
        this.sendResponse(request, { sources: [this.source()] });
        return;
      case "continue":
        this.sendResponse(request, { allThreadsContinued: true });
        await this.resume(false);
        return;
      case "next":
      case "stepIn":
      case "stepOut":
        this.sendResponse(request);
        await this.resume(true);
        return;
      case "disconnect":
      case "terminate":
        this.sendResponse(request);
        this.finish();
        return;
      default:
        this.sendResponse(request);
    }
  }

  async launch(request) {
    this.configuration = { ...this.configuration, ...(request.arguments || {}) };
    if (!hasValue(this.configuration.agentId)) {
      throw new Error("La configuration de débogage doit contenir agentId.");
    }

    const agent = await this.getClient().getAgent(this.configuration.agentId);
    if (this.terminated) {
      return;
    }
    this.agent = agent;
    if (this.agent.is_active === false) {
      throw new Error("Un agent inactif ne peut pas être débogué.");
    }
    this.currentLine = 1;
    this.execution = undefined;
    this.executionPromise = undefined;
    this.executionError = undefined;
    this.resetVariableContainers();
    this.pendingLaunchRequest = request;
    await this.completeLaunchIfReady();
  }

  async completeLaunchIfReady() {
    if (
      this.terminated ||
      this.started ||
      !this.configurationDone ||
      !this.agent ||
      !this.pendingLaunchRequest
    ) {
      return;
    }

    const launchRequest = this.pendingLaunchRequest;
    this.pendingLaunchRequest = undefined;
    this.started = true;
    this.sendResponse(launchRequest);
    if (this.configuration.stopOnEntry !== false || this.breakpoints.has(1)) {
      this.sendStopped("entry");
    } else {
      await this.resume(false);
    }
  }

  setBreakpoints(request) {
    const requested = Array.isArray(request.arguments?.breakpoints)
      ? request.arguments.breakpoints
      : [];
    this.breakpoints.clear();
    const breakpoints = requested.map((breakpoint, index) => {
      const line = Number(breakpoint.line);
      const verified = PHASES.some((phase) => phase.line === line);
      if (verified) {
        this.breakpoints.add(line);
      }
      return {
        id: index + 1,
        verified,
        line,
        source: this.source(),
        ...(!verified
          ? { message: "Choisissez une phase d’exécution comprise entre 1 et 5." }
          : {}),
      };
    });
    this.sendResponse(request, { breakpoints });
  }

  async resume(singleStep) {
    const operation = this.resumeQueue.then(() => this.resumeOnce(singleStep));
    this.resumeQueue = operation.catch(() => undefined);
    return operation;
  }

  async resumeOnce(singleStep) {
    if (this.terminated) {
      return;
    }

    if (this.currentLine >= PHASES.length) {
      this.finishAndNotify();
      return;
    }

    const targetLine = singleStep
      ? Math.min(this.currentLine + 1, PHASES.length)
      : this.nextBreakpointOrEnd();

    if (this.currentLine <= 3 && targetLine > 3 && !this.execution) {
      await this.executeAgent();
      if (this.terminated) {
        return;
      }
    }

    this.currentLine = targetLine;
    this.resetVariableContainers();

    if (this.currentLine >= PHASES.length) {
      if (singleStep || this.breakpoints.has(PHASES.length)) {
        this.sendStopped(singleStep ? "step" : "breakpoint");
      } else {
        this.finishAndNotify();
      }
      return;
    }

    this.sendStopped(singleStep ? "step" : "breakpoint");
  }

  nextBreakpointOrEnd() {
    const next = [...this.breakpoints]
      .filter((line) => line > this.currentLine)
      .sort((left, right) => left - right)[0];
    return next || PHASES.length;
  }

  async executeAgent() {
    if (!this.executionPromise) {
      this.executionPromise = this.executeAgentOnce();
    }
    return this.executionPromise;
  }

  async executeAgentOnce() {
    this.sendEvent("output", {
      category: "console",
      output: `Exécution de ${agentLabel(this.agent)}…\n`,
    });
    let execution;
    try {
      execution = await this.getClient().runAgent(
        this.configuration.agentId,
        String(this.configuration.input || ""),
      );
      if (this.terminated) {
        return;
      }
      const status = String(execution?.status || "").toLowerCase();
      if (status !== "completed") {
        throw new Error(
          `L’exécution n’est pas terminée (statut « ${status || "inconnu"} »).`,
        );
      }
      this.execution = execution;
      this.sendEvent("output", {
        category: "stdout",
        output: `${executionSummary(this.execution)}\n`,
      });
    } catch (error) {
      if (this.terminated) {
        return;
      }
      this.executionError = errorMessage(error);
      this.execution = {
        ...(execution && typeof execution === "object" ? execution : {}),
        agent_id: this.configuration.agentId,
        status: "failed",
        error: this.executionError,
        failure_id: `debug-${Date.now()}-${this.sequence}`,
      };
      this.sendEvent("output", {
        category: "stderr",
        output: `${this.executionError}\n`,
      });
    }
  }

  stackFrame() {
    const phase = PHASES[this.currentLine - 1] || PHASES[0];
    return {
      id: 1,
      name: phase.name,
      line: phase.line,
      column: 1,
      source: this.source(),
    };
  }

  source() {
    return {
      name: `${agentLabel(this.agent)}.agent-world`,
      sourceReference: SOURCE_REFERENCE,
      presentationHint: "normal",
    };
  }

  scopes() {
    return [
      this.createScope("Agent", sanitizeForDebug(this.agent || {}), false),
      this.createScope(
        "Entrée",
        { text: String(this.configuration.input || "") },
        false,
      ),
      this.createScope(
        "Exécution",
        sanitizeForDebug(
          this.execution || { status: "not_started", error: this.executionError },
        ),
        false,
      ),
    ];
  }

  createScope(name, value, expensive) {
    return {
      name,
      variablesReference: this.storeVariableContainer(value),
      expensive,
    };
  }

  variables(reference) {
    const container = this.variableContainers.get(Number(reference));
    if (!container || typeof container !== "object") {
      return [];
    }

    const entries = Array.isArray(container)
      ? container.map((value, index) => [String(index), value])
      : Object.entries(container);
    return entries.map(([name, value]) => this.debugVariable(name, value));
  }

  debugVariable(name, value) {
    const isObject = value !== null && typeof value === "object";
    return {
      name,
      value: displayDebugValue(value),
      type: debugType(value),
      variablesReference: isObject ? this.storeVariableContainer(value) : 0,
    };
  }

  evaluate(request) {
    const expression = String(request.arguments?.expression || "").trim();
    const value = evaluateExpression(expression, {
      agent: sanitizeForDebug(this.agent || {}),
      input: { text: String(this.configuration.input || "") },
      execution: sanitizeForDebug(this.execution || { status: "not_started" }),
    });
    const isObject = value !== null && typeof value === "object";
    this.sendResponse(request, {
      result: displayDebugValue(value),
      type: debugType(value),
      variablesReference: isObject ? this.storeVariableContainer(value) : 0,
    });
  }

  storeVariableContainer(value) {
    const reference = this.nextVariableReference++;
    this.variableContainers.set(reference, value);
    return reference;
  }

  resetVariableContainers() {
    this.variableContainers.clear();
    this.nextVariableReference = 10;
  }

  sendStopped(reason) {
    this.sendEvent("stopped", {
      reason,
      threadId: THREAD_ID,
      allThreadsStopped: true,
    });
  }

  async notifyCompletion() {
    if (!this.notifications || !this.agent) {
      return;
    }
    if (this.executionError) {
      if (this.notifications.notifyTaskFailed) {
        await this.notifications.notifyTaskFailed(
          this.agent,
          this.executionError,
          this.execution,
        );
      } else {
        await this.vscode.window.showErrorMessage(
          `L’exécution de « ${agentLabel(this.agent)} » a échoué : ${this.executionError}`,
        );
      }
      return;
    }
    if (this.notifications.notifyTaskCompleted && this.execution) {
      await this.notifications.notifyTaskCompleted(this.agent, this.execution);
    }
  }

  finishAndNotify() {
    if (this.terminated) {
      return;
    }
    this.finish();
    void this.notifyCompletion().catch(() => undefined);
  }

  finish() {
    if (this.terminated) {
      return;
    }
    this.terminated = true;
    this.sendEvent("terminated");
  }

  sendResponse(request, body = {}) {
    this.messageEmitter.fire({
      type: "response",
      seq: this.sequence++,
      request_seq: request.seq,
      success: true,
      command: request.command,
      body,
    });
  }

  sendErrorResponse(request, error) {
    this.messageEmitter.fire({
      type: "response",
      seq: this.sequence++,
      request_seq: request.seq,
      success: false,
      command: request.command,
      message: errorMessage(error),
      body: { error: { id: 1, format: errorMessage(error), showUser: true } },
    });
  }

  sendEvent(event, body = {}) {
    this.messageEmitter.fire({
      type: "event",
      seq: this.sequence++,
      event,
      body,
    });
  }

  dispose() {
    this.terminated = true;
    this.messageEmitter.dispose();
  }
}

async function startAgentDebugging(vscode, getClient, agent) {
  if (vscode.workspace.isTrusted !== true) {
    await vscode.window.showErrorMessage(
      "Le débogage Agent World est désactivé dans un workspace non approuvé.",
    );
    return false;
  }

  const selectedAgent = validAgent(agent)
    ? agent
    : await chooseAgent(vscode, getClient);
  if (!selectedAgent) {
    return false;
  }
  if (selectedAgent.is_active === false) {
    await vscode.window.showErrorMessage(
      `L’agent « ${agentLabel(selectedAgent)} » est inactif.`,
    );
    return false;
  }

  const input = await vscode.window.showInputBox({
    title: `Agent World — Déboguer ${agentLabel(selectedAgent)}`,
    prompt: "Entrée transmise à l’agent",
    ignoreFocusOut: true,
    validateInput: validateAgentInput,
  });
  if (input === undefined) {
    return false;
  }
  const normalizedInput = input.trim();
  if (!normalizedInput) {
    await vscode.window.showErrorMessage("L’entrée de débogage ne peut pas être vide.");
    return false;
  }

  return vscode.debug.startDebugging(undefined, {
    type: DEBUG_TYPE,
    request: "launch",
    name: `Déboguer ${agentLabel(selectedAgent)}`,
    agentId: selectedAgent.id,
    input: normalizedInput,
    stopOnEntry: true,
  });
}

async function chooseAgent(
  vscode,
  getClient,
  {
    title = "Agent World — Choisir un agent",
    placeHolder = "Sélectionnez l’agent à déboguer",
  } = {},
) {
  let agents;
  try {
    agents = await getClient().getAgents();
  } catch (error) {
    await vscode.window.showErrorMessage(
      `Impossible de charger les agents : ${errorMessage(error)}`,
    );
    return undefined;
  }

  const items = agents.filter(validAgent).map((agent) => ({
    label: agentLabel(agent),
    description: agent.model ? String(agent.model) : undefined,
    detail: agent.is_active === false ? "Agent inactif" : undefined,
    agent,
  }));
  if (items.length === 0) {
    await vscode.window.showInformationMessage("Aucun agent disponible.");
    return undefined;
  }

  const selected = await vscode.window.showQuickPick(items, {
    title,
    placeHolder,
    matchOnDescription: true,
  });
  return selected?.agent;
}

function sourceContent(agent) {
  const name = agentLabel(agent);
  return PHASES.map(
    (phase) => `${phase.line}. ${phase.name}${phase.line === 1 ? ` — ${name}` : ""}`,
  ).join("\n");
}

function sanitizeForDebug(value, seen = new WeakSet()) {
  if (value === null || typeof value !== "object") {
    return value;
  }
  if (seen.has(value)) {
    return "[circular]";
  }
  seen.add(value);

  if (Array.isArray(value)) {
    return value.map((entry) => sanitizeForDebug(entry, seen));
  }

  return Object.fromEntries(
    Object.entries(value).map(([key, entry]) => [
      key,
      SENSITIVE_KEY.test(key) ? "[redacted]" : sanitizeForDebug(entry, seen),
    ]),
  );
}

function evaluateExpression(expression, roots) {
  if (!/^[A-Za-z_$][\w$]*(\.[A-Za-z_$][\w$]*)*$/.test(expression)) {
    throw new Error("Seuls les chemins de variables simples peuvent être évalués.");
  }
  const [root, ...segments] = expression.split(".");
  if (!Object.prototype.hasOwnProperty.call(roots, root)) {
    throw new Error(`Variable inconnue : ${root}`);
  }
  let value = roots[root];
  for (const segment of segments) {
    if (
      value === null ||
      typeof value !== "object" ||
      !Object.prototype.hasOwnProperty.call(value, segment)
    ) {
      throw new Error(`Variable inconnue : ${expression}`);
    }
    value = value[segment];
  }
  return value;
}

function displayDebugValue(value) {
  if (value === undefined) {
    return "undefined";
  }
  if (typeof value === "string") {
    return value;
  }
  if (value !== null && typeof value === "object") {
    return Array.isArray(value)
      ? `Array(${value.length})`
      : `Object(${Object.keys(value).length})`;
  }
  return String(value);
}

function debugType(value) {
  if (Array.isArray(value)) {
    return "array";
  }
  if (value === null) {
    return "null";
  }
  return typeof value;
}

function executionSummary(execution) {
  const id = hasValue(execution?.execution_id)
    ? ` #${execution.execution_id}`
    : "";
  return `Exécution${id} : ${String(execution?.status || "terminée")}`;
}

function validAgent(agent) {
  return Boolean(
    agent &&
      typeof agent === "object" &&
      !Array.isArray(agent) &&
      hasValue(agent.id),
  );
}

function agentLabel(agent) {
  if (hasValue(agent?.name)) {
    return String(agent.name).trim();
  }
  return hasValue(agent?.id) ? `Agent #${agent.id}` : "Agent World";
}

function isUnresolvedVariable(value) {
  return /^\$\{.+\}$/.test(String(value || ""));
}

function validateAgentInput(value) {
  return String(value || "").trim()
    ? undefined
    : "L’entrée ne peut pas être vide.";
}

function hasValue(value) {
  return value !== undefined && value !== null && String(value).trim() !== "";
}

function errorMessage(error) {
  return error instanceof Error ? error.message : String(error || "Erreur inconnue");
}

module.exports = {
  AgentWorldDebugAdapter,
  AgentWorldDebugAdapterFactory,
  AgentWorldDebugConfigurationProvider,
  DEBUG_TYPE,
  PHASES,
  chooseAgent,
  evaluateExpression,
  sanitizeForDebug,
  sourceContent,
  startAgentDebugging,
  validateAgentInput,
};
