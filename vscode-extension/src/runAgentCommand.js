"use strict";

class RunAgentCommand {
  constructor(vscode, { getClient, notificationService }) {
    if (typeof getClient !== "function") {
      throw new TypeError("getClient doit être une fonction.");
    }
    if (
      !notificationService ||
      typeof notificationService.notifyTaskCompleted !== "function"
    ) {
      throw new TypeError("Un service de notifications valide est requis.");
    }

    this.vscode = vscode;
    this.getClient = getClient;
    this.notificationService = notificationService;
  }

  async execute(candidateAgent = undefined, candidateInput = undefined) {
    try {
      const client = this.getClient();
      if (!client || typeof client.runAgent !== "function") {
        throw new Error("Le client Agent World ne permet pas d’exécuter un agent.");
      }

      const agent =
        unwrapAgent(candidateAgent) || (await this.selectAgent(client));
      if (!agent) {
        return { status: "cancelled" };
      }
      assertAgentIdentifier(agent);

      const input = await this.resolveInput(candidateInput, agent);
      if (input === undefined) {
        return { status: "cancelled" };
      }

      const execution = await client.runAgent(agent.id, input);
      assertExecution(execution, agent.id);

      const status = String(execution.status || "").toLowerCase();
      if (status === "failed" || status === "cancelled") {
        throw new Error(
          firstDisplayText(
            execution.error_message,
            execution.error,
            `L’exécution s’est terminée avec le statut « ${status} ».`,
          ),
        );
      }
      if (status !== "completed") {
        throw new Error(
          `L’exécution n’est pas terminée (statut « ${status || "inconnu"} »).`,
        );
      }

      const notification = await this.notificationService.notifyTaskCompleted(
        agent,
        execution,
      );
      return {
        status: "completed",
        agent,
        execution,
        notification,
      };
    } catch (error) {
      const detail = errorMessage(error);
      try {
        await this.vscode.window.showErrorMessage(
          `Impossible d’exécuter l’agent : ${detail}`,
        );
      } catch (_notificationError) {
        // Preserve the execution error in the returned result.
      }
      return { status: "error", error };
    }
  }

  async selectAgent(client) {
    if (typeof client.getAgents !== "function") {
      throw new Error("Le client Agent World ne permet pas de lister les agents.");
    }

    const payload = await client.getAgents();
    if (!Array.isArray(payload)) {
      throw new Error("La réponse de l’API pour les agents n’est pas une liste.");
    }

    const items = payload
      .filter(isSelectableAgent)
      .map((agent) => ({
        label: agentLabel(agent),
        description: firstDisplayText(agent.model, `Agent #${agent.id}`),
        detail: firstDisplayText(agent.description),
        agent,
      }));

    if (items.length === 0) {
      await this.vscode.window.showInformationMessage(
        "Aucun agent Agent World n’est disponible.",
      );
      return undefined;
    }

    const selected = await this.vscode.window.showQuickPick(items, {
      title: "Agent World — Exécuter un agent",
      placeHolder: "Choisissez l’agent à exécuter",
      matchOnDescription: true,
      matchOnDetail: true,
      ignoreFocusOut: true,
    });
    return selected ? selected.agent : undefined;
  }

  async resolveInput(candidateInput, agent) {
    if (candidateInput !== undefined && candidateInput !== null) {
      const input = String(candidateInput).trim();
      if (!input) {
        throw new Error("La consigne de l’agent ne peut pas être vide.");
      }
      return input;
    }

    const input = await this.vscode.window.showInputBox({
      title: `Exécuter ${agentLabel(agent)}`,
      prompt: "Saisissez la consigne à transmettre à l’agent.",
      placeHolder: "Décrivez la tâche à accomplir",
      ignoreFocusOut: true,
      validateInput: (value) =>
        String(value || "").trim()
          ? undefined
          : "La consigne ne peut pas être vide.",
    });

    if (input === undefined) {
      return undefined;
    }
    const normalized = input.trim();
    if (!normalized) {
      throw new Error("La consigne de l’agent ne peut pas être vide.");
    }
    return normalized;
  }
}

function unwrapAgent(candidate) {
  if (!candidate || typeof candidate !== "object" || Array.isArray(candidate)) {
    return undefined;
  }
  if (
    candidate.kind === "agent" &&
    candidate.agent &&
    typeof candidate.agent === "object" &&
    !Array.isArray(candidate.agent)
  ) {
    return candidate.agent;
  }
  return candidate;
}

function isSelectableAgent(agent) {
  return Boolean(
    agent &&
      typeof agent === "object" &&
      !Array.isArray(agent) &&
      agent.id !== undefined &&
      agent.id !== null &&
      String(agent.id).trim(),
  );
}

function assertAgentIdentifier(agent) {
  if (!isSelectableAgent(agent)) {
    throw new Error("L’agent sélectionné ne possède pas d’identifiant valide.");
  }
}

function assertExecution(execution, agentId) {
  if (!execution || typeof execution !== "object" || Array.isArray(execution)) {
    throw new Error("La réponse d’exécution de l’API est invalide.");
  }
  if (
    execution.execution_id === undefined ||
    execution.execution_id === null ||
    String(execution.execution_id).trim() === ""
  ) {
    throw new Error("La réponse d’exécution ne contient pas d’identifiant.");
  }
  if (
    execution.agent_id !== undefined &&
    execution.agent_id !== null &&
    String(execution.agent_id) !== String(agentId)
  ) {
    throw new Error("La réponse d’exécution concerne un autre agent.");
  }
}

function agentLabel(agent) {
  return firstDisplayText(agent && agent.name, `Agent #${agent && agent.id}`);
}

function firstDisplayText(...values) {
  for (const value of values) {
    if (value !== undefined && value !== null && String(value).trim() !== "") {
      return String(value).trim();
    }
  }
  return "Agent";
}

function errorMessage(error) {
  return error instanceof Error ? error.message : String(error || "Erreur inconnue");
}

module.exports = {
  RunAgentCommand,
  agentLabel,
  isSelectableAgent,
  unwrapAgent,
};
