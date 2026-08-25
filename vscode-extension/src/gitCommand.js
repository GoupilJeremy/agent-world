"use strict";

const { chooseAgent } = require("./debugAdapter");
const { unwrapAgent } = require("./runAgentCommand");

/**
 * Resolve an agent for a Git command without performing any API call in an
 * untrusted workspace.
 */
async function withSelectedAgent(vscode, getClient, candidate, action) {
  if (vscode.workspace.isTrusted !== true) {
    const error = new Error(
      "Les opérations Git sont désactivées dans un workspace non approuvé.",
    );
    try {
      await vscode.window.showErrorMessage(error.message);
    } catch (_notificationError) {
      // The command still returns a stable error result if VS Code cannot notify.
    }
    return { status: "error", error };
  }

  const suppliedAgent = unwrapAgent(candidate);
  const agent = suppliedAgent ||
    (await chooseAgent(vscode, getClient, {
      title: "Agent World — Choisir un agent",
      placeHolder: "Sélectionnez l’agent à associer à l’opération Git",
    }));
  if (!agent) {
    return { status: "cancelled" };
  }
  return action(agent);
}

module.exports = { withSelectedAgent };
