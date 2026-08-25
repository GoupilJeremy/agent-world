"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const {
  COMMAND_DEFINITIONS,
  VscodeCommandService,
} = require("../src/vscodeCommandService");

test("la liste autorisée expose au moins trois commandes VS Code fixes", () => {
  assert.ok(COMMAND_DEFINITIONS.length >= 3);
  assert.deepEqual(
    COMMAND_DEFINITIONS.map((definition) => definition.commandId),
    [
      "editor.action.formatDocument",
      "editor.action.organizeImports",
      "workbench.action.files.saveAll",
    ],
  );
});

test("le picker exécute uniquement l’action autorisée sélectionnée", async () => {
  const fixture = createFixture({ selectedActionId: "organizeImports" });
  const service = new VscodeCommandService(fixture.vscode);

  const result = await service.pickAndExecute();

  assert.equal(result.status, "executed");
  assert.equal(result.actionId, "organizeImports");
  assert.deepEqual(fixture.executedCommands, ["editor.action.organizeImports"]);
  assert.equal(fixture.pickerItems.length, 3);
});

test("l’annulation du picker n’exécute aucune commande", async () => {
  const fixture = createFixture({ selectedActionId: undefined });
  const service = new VscodeCommandService(fixture.vscode);

  const result = await service.pickAndExecute();

  assert.equal(result.status, "cancelled");
  assert.deepEqual(fixture.executedCommands, []);
});

test("un identifiant hors allowlist est refusé sans atteindre VS Code", async () => {
  const fixture = createFixture();
  const service = new VscodeCommandService(fixture.vscode);

  const result = await service.execute("workbench.action.closeAllEditors");

  assert.equal(result.status, "error");
  assert.deepEqual(fixture.executedCommands, []);
  assert.match(fixture.errors[0], /liste autorisée/);
});

test("une action d’éditeur exige un document actif", async () => {
  const fixture = createFixture({ activeTextEditor: undefined });
  const service = new VscodeCommandService(fixture.vscode);

  const result = await service.execute("formatDocument");

  assert.equal(result.status, "error");
  assert.deepEqual(fixture.executedCommands, []);
  assert.match(fixture.errors[0], /Ouvrez un fichier/);
});

test("les commandes sont refusées dans un workspace non approuvé", async () => {
  const fixture = createFixture({ isTrusted: false });
  const service = new VscodeCommandService(fixture.vscode);

  const result = await service.execute("saveAll");

  assert.equal(result.status, "error");
  assert.deepEqual(fixture.executedCommands, []);
  assert.match(fixture.errors[0], /workspace non approuvé/);
});

test("une erreur renvoyée par la commande VS Code est présentée", async () => {
  const fixture = createFixture({ commandError: new Error("Formatter indisponible") });
  const service = new VscodeCommandService(fixture.vscode);

  const result = await service.execute("formatDocument");

  assert.equal(result.status, "error");
  assert.deepEqual(fixture.executedCommands, ["editor.action.formatDocument"]);
  assert.match(fixture.errors[0], /Formatter indisponible/);
});

function createFixture(options = {}) {
  const executedCommands = [];
  const errors = [];
  let pickerItems = [];
  const hasEditorOverride = Object.prototype.hasOwnProperty.call(
    options,
    "activeTextEditor",
  );
  const activeTextEditor = hasEditorOverride
    ? options.activeTextEditor
    : { document: { isClosed: false } };

  const vscode = {
    workspace: { isTrusted: options.isTrusted !== false },
    window: {
      activeTextEditor,
      async showQuickPick(items) {
        pickerItems = items;
        return items.find((item) => item.actionId === options.selectedActionId);
      },
      async showErrorMessage(message) {
        errors.push(message);
      },
    },
    commands: {
      async executeCommand(commandId) {
        executedCommands.push(commandId);
        if (options.commandError) {
          throw options.commandError;
        }
      },
    },
  };

  return {
    vscode,
    executedCommands,
    errors,
    get pickerItems() {
      return pickerItems;
    },
  };
}
