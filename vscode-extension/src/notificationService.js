"use strict";

const COMPLETION_STORAGE_KEY = "agentWorld.completedExecutionNotifications";
const VIEW_AGENT_ACTION = "Afficher l’agent";
const DEFAULT_MAX_ENTRIES = 200;

class NotificationService {
  constructor(
    vscode,
    {
      state = undefined,
      openAgentDetail = undefined,
      maxEntries = DEFAULT_MAX_ENTRIES,
      scope = undefined,
    } = {},
  ) {
    this.vscode = vscode;
    this.state = state;
    this.maxEntries = normalizeMaxEntries(maxEntries);
    this.scope = scope;
    this.pendingKeys = new Set();
    this.openAgentDetail =
      openAgentDetail ||
      ((agent) =>
        this.vscode.commands.executeCommand("agentWorld.openAgentDetail", agent));

    const persisted = readPersistedKeys(state);
    this.keyOrder = persisted.slice(-this.maxEntries);
    this.seenKeys = new Set(this.keyOrder);
  }

  async notifyTaskCompleted(agent, execution) {
    let pendingKey;
    try {
      const key = this.scopedKey(completionKey(agent, execution));
      if (this.seenKeys.has(key) || this.pendingKeys.has(key)) {
        return { status: "duplicate", key };
      }

      this.pendingKeys.add(key);
      pendingKey = key;
      const choice = await this.vscode.window.showInformationMessage(
        completionMessage(agent),
        VIEW_AGENT_ACTION,
      );
      await this.remember(key);

      if (choice === VIEW_AGENT_ACTION) {
        await this.openAgentDetail(agent);
        return { status: "opened", key };
      }

      return { status: "notified", key };
    } catch (error) {
      const detail = errorMessage(error);
      try {
        await this.vscode.window.showErrorMessage(
          `Impossible d’afficher la notification Agent World : ${detail}`,
        );
      } catch (_notificationError) {
        // Preserve the original failure in the returned result.
      }
      return { status: "error", error };
    } finally {
      if (pendingKey) {
        this.pendingKeys.delete(pendingKey);
      }
    }
  }

  async notifyTaskFailed(agent, failure, execution = undefined) {
    let pendingKey;
    try {
      const detail = errorMessage(failure);
      const key = this.scopedKey(failureKey(agent, execution, detail));
      if (this.seenKeys.has(key) || this.pendingKeys.has(key)) {
        return { status: "duplicate", key };
      }

      this.pendingKeys.add(key);
      pendingKey = key;
      const choice = await this.vscode.window.showErrorMessage(
        failureMessage(agent, detail),
        VIEW_AGENT_ACTION,
      );
      await this.remember(key);

      if (choice === VIEW_AGENT_ACTION) {
        await this.openAgentDetail(agent);
        return { status: "opened", key };
      }

      return { status: "notified", key };
    } catch (error) {
      const detail = errorMessage(error);
      try {
        await this.vscode.window.showErrorMessage(
          `Impossible d’afficher la notification Agent World : ${detail}`,
        );
      } catch (_notificationError) {
        // Preserve the original failure in the returned result.
      }
      return { status: "error", error };
    } finally {
      if (pendingKey) {
        this.pendingKeys.delete(pendingKey);
      }
    }
  }

  scopedKey(key) {
    const scope = typeof this.scope === "function" ? this.scope() : this.scope;
    const normalizedScope = firstDisplayText(scope);
    return normalizedScope
      ? `scope:${stableStringHash(normalizedScope)}:${key}`
      : key;
  }

  async remember(key) {
    this.seenKeys.add(key);
    this.keyOrder.push(key);

    while (this.keyOrder.length > this.maxEntries) {
      const oldest = this.keyOrder.shift();
      this.seenKeys.delete(oldest);
    }

    if (this.state && typeof this.state.update === "function") {
      try {
        await this.state.update(COMPLETION_STORAGE_KEY, [...this.keyOrder]);
      } catch (_error) {
        // In-memory de-duplication remains available when persistence is unavailable.
      }
    }
  }
}

function completionKey(agent, execution) {
  if (!execution || typeof execution !== "object" || Array.isArray(execution)) {
    throw new Error("Les informations d’exécution sont invalides.");
  }

  const executionId = firstDisplayText(execution.execution_id, execution.id);
  if (!executionId) {
    throw new Error("Un identifiant d’exécution est requis pour la déduplication.");
  }

  const agentId = firstDisplayText(agent && agent.id, execution.agent_id, "unknown");
  return `agent:${agentId}:execution:${executionId}:completed`;
}

function completionMessage(agent) {
  const name = firstDisplayText(agent && agent.name);
  return name
    ? `Agent World : la tâche de « ${name} » est terminée.`
    : "Agent World : la tâche de l’agent est terminée.";
}

function failureKey(agent, execution, detail) {
  const agentId = firstDisplayText(agent && agent.id, execution && execution.agent_id);
  const executionId = firstDisplayText(
    execution && execution.execution_id,
    execution && execution.id,
    execution && execution.failure_id,
  );
  const identity = executionId || stableStringHash(detail);
  return `agent:${agentId || "unknown"}:execution:${identity}:failed`;
}

function failureMessage(agent, detail) {
  const name = firstDisplayText(agent && agent.name);
  const subject = name ? `La tâche de « ${name} »` : "La tâche de l’agent";
  return `Agent World : ${subject} a échoué — ${detail}`;
}

function stableStringHash(value) {
  let hash = 2166136261;
  for (const character of String(value)) {
    hash ^= character.codePointAt(0);
    hash = Math.imul(hash, 16777619);
  }
  return (hash >>> 0).toString(16).padStart(8, "0");
}

function readPersistedKeys(state) {
  if (!state || typeof state.get !== "function") {
    return [];
  }

  const persisted = state.get(COMPLETION_STORAGE_KEY, []);
  if (!Array.isArray(persisted)) {
    return [];
  }
  return [...new Set(persisted.filter((key) => typeof key === "string" && key))];
}

function normalizeMaxEntries(value) {
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) && parsed > 0
    ? parsed
    : DEFAULT_MAX_ENTRIES;
}

function firstDisplayText(...values) {
  for (const value of values) {
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      return String(value).trim();
    }
  }
  return "";
}

function errorMessage(error) {
  return error instanceof Error ? error.message : String(error || "Erreur inconnue");
}

module.exports = {
  COMPLETION_STORAGE_KEY,
  NotificationService,
  VIEW_AGENT_ACTION,
  completionKey,
  failureKey,
};
