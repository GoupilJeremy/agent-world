"use strict";

const COMMAND_DEFINITIONS = Object.freeze([
  Object.freeze({
    id: "formatDocument",
    label: "$(symbol-method) Formater le document actif",
    description: "Appliquer le formateur configuré pour le document courant",
    commandId: "editor.action.formatDocument",
    requiresEditor: true,
  }),
  Object.freeze({
    id: "organizeImports",
    label: "$(list-tree) Organiser les imports",
    description: "Organiser les imports du document courant",
    commandId: "editor.action.organizeImports",
    requiresEditor: true,
  }),
  Object.freeze({
    id: "saveAll",
    label: "$(save-all) Enregistrer tous les fichiers",
    description: "Enregistrer tous les éditeurs contenant des modifications",
    commandId: "workbench.action.files.saveAll",
    requiresEditor: false,
  }),
]);

class VscodeCommandService {
  constructor(vscode, { definitions = COMMAND_DEFINITIONS } = {}) {
    this.vscode = vscode;
    this.definitions = new Map(
      definitions.map((definition) => [definition.id, definition]),
    );
  }

  listCommands() {
    return [...this.definitions.values()];
  }

  async pickAndExecute() {
    try {
      this.assertTrustedWorkspace();
      const selected = await this.vscode.window.showQuickPick(
        this.listCommands().map((definition) => ({
          label: definition.label,
          description: definition.description,
          actionId: definition.id,
        })),
        {
          title: "Agent World — Exécuter une commande VS Code",
          placeHolder: "Choisissez une action autorisée",
          matchOnDescription: true,
          ignoreFocusOut: true,
        },
      );

      if (!selected) {
        return { status: "cancelled" };
      }

      return await this.executeAllowedCommand(selected.actionId);
    } catch (error) {
      return this.reportError(error);
    }
  }

  async execute(actionId) {
    try {
      this.assertTrustedWorkspace();
      return await this.executeAllowedCommand(actionId);
    } catch (error) {
      return this.reportError(error);
    }
  }

  async executeAllowedCommand(actionId) {
    const definition = this.definitions.get(actionId);
    if (!definition) {
      throw new Error("Cette commande ne fait pas partie de la liste autorisée.");
    }

    if (definition.requiresEditor) {
      const document = this.vscode.window.activeTextEditor?.document;
      if (!document || document.isClosed === true) {
        throw new Error("Ouvrez un fichier dans l’éditeur avant cette action.");
      }
    }

    await this.vscode.commands.executeCommand(definition.commandId);
    return {
      status: "executed",
      actionId: definition.id,
      commandId: definition.commandId,
    };
  }

  assertTrustedWorkspace() {
    if (this.vscode.workspace.isTrusted !== true) {
      throw new Error(
        "Les commandes Agent World sont désactivées dans un workspace non approuvé.",
      );
    }
  }

  async reportError(error) {
    const detail = errorMessage(error);
    try {
      await this.vscode.window.showErrorMessage(
        `Impossible d’exécuter la commande VS Code : ${detail}`,
      );
    } catch (_notificationError) {
      // The original command error remains the useful result for callers.
    }
    return { status: "error", error };
  }
}

function errorMessage(error) {
  return error instanceof Error ? error.message : String(error || "Erreur inconnue");
}

module.exports = {
  COMMAND_DEFINITIONS,
  VscodeCommandService,
};
