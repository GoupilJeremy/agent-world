"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const {
  ASSOCIATIONS_STORAGE_KEY,
  COMMIT_CONFIRM_ACTION,
  GitIntegration,
  MAX_SUGGESTED_MESSAGE_LENGTH,
  PUSH_CONFIRM_ACTION,
  collectUnstagedResources,
  getChangeSummary,
  suggestCommitMessage,
} = require("../src/gitIntegration");

test("la suggestion de commit est sûre, descriptive et bornée", () => {
  const message = suggestCommitMessage(
    { name: `Analyse\nmalveillante ${"x".repeat(100)}` },
    { total: 3 },
  );

  assert.match(message, /^chore: update Analyse malveillante/);
  assert.doesNotMatch(message, /[\r\n]/);
  assert.ok(message.length <= MAX_SUGGESTED_MESSAGE_LENGTH);
  assert.match(suggestCommitMessage({ name: "Résumé" }, { total: 1 }), /output$/);
});

test("le résumé suit le contrat RepositoryState public de vscode.git", () => {
  const repository = createRepository("demo", {
    working: ["a.md", "new.md"],
    staged: ["c.md"],
    merge: ["conflict.md"],
  });

  assert.equal(
    Object.hasOwn(repository.state, "untrackedChanges"),
    false,
    "les fichiers non suivis sont exposés dans workingTreeChanges",
  );
  assert.deepEqual(getChangeSummary(repository), {
    workingTree: 2,
    staged: 1,
    merge: 1,
    total: 4,
    hasChanges: true,
  });
  assert.deepEqual(collectUnstagedResources(repository), [
    "/workspace/demo/a.md",
    "/workspace/demo/new.md",
  ]);
});

test("initialize active vscode.git et relaie state.onDidChange", async () => {
  const first = createRepository("first", { working: ["one.md"] });
  const openedSecond = createRepository("second");
  const closedSecondWrapper = createRepository("second");
  const harness = createHarness({
    repositories: [first],
    gitInitiallyActive: false,
  });
  const integration = new GitIntegration(harness.vscode, harness.storage);
  const events = [];
  integration.onDidChangeRepository((event) => events.push(event));

  assert.equal(await integration.initialize(), true);
  assert.equal(harness.calls.extensionActivate, 1);

  first.state.workingTreeChanges.push(first.makeChange("two.md"));
  first.emitChange();
  assert.equal(events.length, 1);
  assert.equal(events[0].repository, first);
  assert.equal(events[0].summary.workingTree, 2);

  harness.gitApi.repositories.push(openedSecond);
  harness.gitApi.emitOpen(openedSecond);
  openedSecond.state.indexChanges.push(openedSecond.makeChange("staged.md"));
  openedSecond.emitChange();
  assert.equal(events.length, 2);
  assert.equal(events[1].repository, openedSecond);

  assert.notEqual(openedSecond, closedSecondWrapper);
  harness.gitApi.emitClose(closedSecondWrapper);
  openedSecond.emitChange();
  assert.equal(
    events.length,
    2,
    "la fermeture doit retrouver le listener par URI, même avec un autre wrapper",
  );

  integration.dispose();
  first.emitChange();
  harness.gitApi.emitOpen(createRepository("late"));
  assert.equal(events.length, 2, "dispose arrête tous les listeners Git");
});

test("l'association multi-repo est choisie puis persistée par agent", async () => {
  const first = createRepository("first");
  const second = createRepository("second");
  const harness = createHarness({
    repositories: [first, second],
    quickPickIndex: 1,
  });
  const integration = new GitIntegration(harness.vscode, harness.storage);

  const result = await integration.linkAgentToRepository({
    id: 7,
    name: "Analyse",
  });

  assert.equal(result.status, "linked");
  assert.equal(result.repository, second);
  assert.equal(harness.calls.quickPick.length, 1);
  assert.equal(harness.calls.quickPick[0].kind, "repository");
  assert.equal(
    harness.storage.values[ASSOCIATIONS_STORAGE_KEY]["id:7"],
    second.rootUri.toString(),
  );
  assert.equal(
    await integration.getLinkedRepository({ id: 7, name: "Renommé" }),
    second,
  );
});

test("un dépôt unique est associé sans QuickPick", async () => {
  const repository = createRepository("only");
  const harness = createHarness({ repositories: [repository] });
  const integration = new GitIntegration(harness.vscode, harness.storage);

  const result = await integration.linkAgentToRepository({ id: 2, name: "Agent" });

  assert.equal(result.status, "linked");
  assert.equal(harness.calls.quickPick.length, 0);
  assert.equal(
    harness.storage.values[ASSOCIATIONS_STORAGE_KEY]["id:2"],
    repository.rootUri.toString(),
  );
});

test("l'association Git est refusée dans un workspace non approuvé", async () => {
  const repository = createRepository("only");
  const harness = createHarness({ repositories: [repository], trusted: false });
  const integration = new GitIntegration(harness.vscode, harness.storage);

  const result = await integration.linkAgentToRepository({ id: 2, name: "Agent" });

  assert.equal(result.status, "error");
  assert.match(harness.calls.errors[0], /non approuv/);
  assert.equal(harness.calls.storageUpdates.length, 0);
});

test("l'absence de Git et l'annulation multi-repo échouent proprement", async (t) => {
  await t.test("extension Git absente", async () => {
    const harness = createHarness({ gitAvailable: false });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    assert.equal(await integration.initialize(), false);
    const result = await integration.linkAgentToRepository({ id: 1 });

    assert.equal(result.status, "error");
    assert.match(harness.calls.errors[0], /indisponible/);
    assert.equal(harness.calls.storageUpdates.length, 0);
  });

  await t.test("choix annulé", async () => {
    const harness = createHarness({
      repositories: [createRepository("one"), createRepository("two")],
      quickPickIndex: null,
    });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.linkAgentToRepository({ id: 1 });

    assert.deepEqual(result, { status: "cancelled" });
    assert.equal(harness.calls.storageUpdates.length, 0);
    assert.equal(harness.calls.information.length, 0);
  });
});

test("stageAndCommit indexe uniquement les fichiers explicitement sélectionnés", async () => {
  const repository = createRepository("project", {
    working: ["generated/a.md", "generated/b.md", "generated/new.md"],
  });
  const harness = createHarness({
    repositories: [repository],
    fileSelectionIndices: [0, 2],
    warningResults: [COMMIT_CONFIRM_ACTION],
    inputResult: "feat: publish agent output",
  });
  const integration = new GitIntegration(harness.vscode, harness.storage);

  const result = await integration.stageAndCommit({ id: 3, name: "Writer" });

  assert.equal(result.status, "committed");
  assert.equal(result.message, "feat: publish agent output");
  assert.equal(result.staged, 2);
  assert.deepEqual(repository.calls.add, [
    [
      "/workspace/project/generated/a.md",
      "/workspace/project/generated/new.md",
    ],
  ]);
  assert.deepEqual(repository.calls.commit, [
    {
      message: "feat: publish agent output",
      options: { postCommitCommand: null },
    },
  ]);
  const changePicker = harness.calls.quickPick.find(
    (call) => call.kind === "changes",
  );
  assert.ok(changePicker);
  assert.equal(changePicker.options.canPickMany, true);
  assert.deepEqual(
    changePicker.items.map((item) => item.label),
    ["generated/a.md", "generated/b.md", "generated/new.md"],
  );
  assert.match(harness.calls.input[0].value, /^chore: update Writer outputs/);
  assert.match(harness.calls.warning[0].message, /2 changements/);
  assert.deepEqual(harness.calls.warning[0].options, { modal: true });
  assert.equal(
    harness.storage.values[ASSOCIATIONS_STORAGE_KEY]["id:3"],
    repository.rootUri.toString(),
  );
});

test("stageAndCommit réutilise l'association sans re-sélectionner le dépôt", async () => {
  const first = createRepository("first", { working: ["wrong.md"] });
  const second = createRepository("second", { working: ["ready.md"] });
  const storageValues = {
    [ASSOCIATIONS_STORAGE_KEY]: { "id:9": second.rootUri.toString() },
  };
  const harness = createHarness({
    repositories: [first, second],
    storageValues,
    warningResults: [COMMIT_CONFIRM_ACTION],
  });
  const integration = new GitIntegration(harness.vscode, harness.storage);

  const result = await integration.stageAndCommit({ id: 9, name: "Linked" });

  assert.equal(result.status, "committed");
  assert.equal(result.repository, second);
  assert.equal(
    harness.calls.quickPick.filter((call) => call.kind === "repository").length,
    0,
  );
  assert.equal(first.calls.commit.length, 0);
  assert.deepEqual(second.calls.add, [["/workspace/second/ready.md"]]);
  assert.equal(second.calls.commit.length, 1);
});

test("stageAndCommit refuse tout index préexistant", async () => {
  const repository = createRepository("repo", {
    working: ["agent.md"],
    staged: ["unrelated.md"],
  });
  const harness = createHarness({ repositories: [repository] });
  const integration = new GitIntegration(harness.vscode, harness.storage);

  const result = await integration.stageAndCommit({ id: 1 });

  assert.equal(result.status, "error");
  assert.match(harness.calls.errors[0], /Désindexez/);
  assert.equal(harness.calls.quickPick.length, 0);
  assert.equal(harness.calls.warning.length, 0);
  assert.equal(repository.calls.add.length, 0);
  assert.equal(repository.calls.commit.length, 0);
});

test("stageAndCommit recontrôle l'index juste avant l'ajout", async () => {
  const repository = createRepository("repo", { working: ["agent.md"] });
  const harness = createHarness({
    repositories: [repository],
    warningResults: [COMMIT_CONFIRM_ACTION],
    onShowInputBox() {
      repository.state.indexChanges.push(repository.makeChange("concurrent.md"));
    },
  });
  const integration = new GitIntegration(harness.vscode, harness.storage);

  const result = await integration.stageAndCommit({ id: 1 });

  assert.equal(result.status, "error");
  assert.match(harness.calls.errors[0], /index Git a changé/);
  assert.equal(repository.calls.add.length, 0);
  assert.equal(repository.calls.commit.length, 0);
});

test("stageAndCommit exige une sélection explicite non vide", async (t) => {
  await t.test("sélecteur annulé", async () => {
    const repository = createRepository("repo", { working: ["a.md"] });
    const harness = createHarness({
      repositories: [repository],
      fileSelectionIndices: null,
    });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.stageAndCommit({ id: 1 });

    assert.equal(result.status, "cancelled");
    assert.equal(harness.calls.warning.length, 0);
    assert.equal(repository.calls.add.length, 0);
    assert.equal(repository.calls.commit.length, 0);
  });

  await t.test("sélection vide", async () => {
    const repository = createRepository("repo", { working: ["a.md"] });
    const harness = createHarness({
      repositories: [repository],
      fileSelectionIndices: [],
    });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.stageAndCommit({ id: 1 });

    assert.equal(result.status, "cancelled");
    assert.equal(harness.calls.warning.length, 0);
    assert.equal(repository.calls.add.length, 0);
    assert.equal(repository.calls.commit.length, 0);
  });
});

test("stageAndCommit n'écrit rien après refus, annulation ou workspace non approuvé", async (t) => {
  await t.test("confirmation refusée", async () => {
    const repository = createRepository("repo", { working: ["a.md"] });
    const harness = createHarness({
      repositories: [repository],
      warningResults: [undefined],
    });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.stageAndCommit({ id: 1 });

    assert.equal(result.status, "cancelled");
    assert.equal(harness.calls.input.length, 0);
    assert.equal(repository.calls.add.length, 0);
    assert.equal(repository.calls.commit.length, 0);
  });

  await t.test("saisie annulée", async () => {
    const repository = createRepository("repo", { working: ["a.md"] });
    const harness = createHarness({
      repositories: [repository],
      warningResults: [COMMIT_CONFIRM_ACTION],
      inputResult: CANCEL_INPUT,
    });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.stageAndCommit({ id: 1 });

    assert.equal(result.status, "cancelled");
    assert.equal(repository.calls.add.length, 0);
    assert.equal(repository.calls.commit.length, 0);
  });

  await t.test("workspace non approuvé", async () => {
    const repository = createRepository("repo", { working: ["a.md"] });
    const harness = createHarness({ repositories: [repository], trusted: false });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.stageAndCommit({ id: 1 });

    assert.equal(result.status, "error");
    assert.match(harness.calls.errors[0], /non approuv/);
    assert.equal(
      harness.calls.getExtension,
      0,
      "Git n'est pas consulté avant le trust guard",
    );
    assert.equal(harness.calls.warning.length, 0);
    assert.equal(repository.calls.add.length, 0);
    assert.equal(repository.calls.commit.length, 0);
  });
});

test("stageAndCommit traite l'absence de changement et les conflits sans mutation", async (t) => {
  await t.test("aucun changement", async () => {
    const repository = createRepository("clean");
    const harness = createHarness({ repositories: [repository] });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.stageAndCommit({ id: 1 });

    assert.equal(result.status, "no_changes");
    assert.match(harness.calls.information[0], /Aucun changement/);
    assert.equal(harness.calls.warning.length, 0);
  });

  await t.test("conflit non résolu", async () => {
    const repository = createRepository("conflicted", { merge: ["a.md"] });
    const harness = createHarness({ repositories: [repository] });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.stageAndCommit({ id: 1 });

    assert.equal(result.status, "error");
    assert.match(harness.calls.errors[0], /conflits/);
    assert.equal(harness.calls.warning.length, 0);
    assert.equal(repository.calls.commit.length, 0);
  });
});

test("push confirme la cible et appelle la signature publique sans force", async (t) => {
  await t.test("upstream existant", async () => {
    const repository = createRepository("remote-ready");
    const harness = createHarness({
      repositories: [repository],
      warningResults: [PUSH_CONFIRM_ACTION],
    });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.push({ id: 4, name: "Publisher" });

    assert.equal(result.status, "pushed");
    assert.deepEqual(
      repository.calls.push,
      [[]],
      "un upstream existant est respecté via push() sans reconstruction",
    );
    assert.deepEqual(harness.calls.warning[0].options, { modal: true });
    assert.match(harness.calls.warning[0].message, /origin\/main/);
    assert.doesNotMatch(harness.calls.warning[0].message, /origin\/origin\/main/);
    assert.match(harness.calls.information[0], /pouss/);
  });

  await t.test("push annulé", async () => {
    const repository = createRepository("remote-ready");
    const harness = createHarness({
      repositories: [repository],
      warningResults: [undefined],
    });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.push({ id: 4 });

    assert.equal(result.status, "cancelled");
    assert.equal(repository.calls.push.length, 0);
  });

  await t.test("erreur API Git", async () => {
    const repository = createRepository("remote-error", { pushError: "offline" });
    const harness = createHarness({
      repositories: [repository],
      warningResults: [PUSH_CONFIRM_ACTION],
    });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.push({ id: 4 });

    assert.equal(result.status, "error");
    assert.match(harness.calls.errors[0], /offline/);
    assert.equal(repository.calls.push.length, 1);
  });
});

test("push effectue le préflight HEAD, remotes et upstream", async (t) => {
  await t.test("HEAD absent", async () => {
    const repository = createRepository("detached", { head: null });
    const harness = createHarness({ repositories: [repository] });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.push({ id: 1 });

    assert.equal(result.status, "error");
    assert.match(harness.calls.errors[0], /branche Git active/);
    assert.equal(harness.calls.warning.length, 0);
    assert.equal(repository.calls.push.length, 0);
  });

  await t.test("aucun remote inscriptible", async () => {
    const repository = createRepository("read-only", {
      remotes: [createRemote("origin", { isReadOnly: true })],
    });
    const harness = createHarness({ repositories: [repository] });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.push({ id: 1 });

    assert.equal(result.status, "error");
    assert.match(harness.calls.errors[0], /écriture/);
    assert.equal(harness.calls.warning.length, 0);
    assert.equal(repository.calls.push.length, 0);
  });

  await t.test("remote upstream indisponible", async () => {
    const repository = createRepository("missing-upstream", {
      head: createHead("main", { remote: "gone", name: "main" }),
      remotes: [createRemote("origin")],
    });
    const harness = createHarness({ repositories: [repository] });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.push({ id: 1 });

    assert.equal(result.status, "error");
    assert.match(harness.calls.errors[0], /upstream/);
    assert.equal(repository.calls.push.length, 0);
  });
});

test("push configure explicitement l'upstream sans forcer", async (t) => {
  await t.test("remote unique", async () => {
    const repository = createRepository("new-branch", {
      head: createHead("feature/agent"),
      remotes: [createRemote("origin")],
    });
    const harness = createHarness({
      repositories: [repository],
      warningResults: [PUSH_CONFIRM_ACTION],
    });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.push({ id: 1 });

    assert.equal(result.status, "pushed");
    assert.deepEqual(repository.calls.push, [
      ["origin", "feature/agent", true],
    ]);
    assert.match(harness.calls.warning[0].message, /configurer son upstream/);
  });

  await t.test("choix explicite parmi plusieurs remotes", async () => {
    const repository = createRepository("multi-remote", {
      head: createHead("topic"),
      remotes: [createRemote("origin"), createRemote("fork")],
    });
    const harness = createHarness({
      repositories: [repository],
      remotePickIndex: 1,
      warningResults: [PUSH_CONFIRM_ACTION],
    });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.push({ id: 1 });

    assert.equal(result.status, "pushed");
    assert.equal(harness.calls.quickPick[0].kind, "remote");
    assert.deepEqual(repository.calls.push, [["fork", "topic", true]]);
  });

  await t.test("choix du remote annulé", async () => {
    const repository = createRepository("multi-remote", {
      head: createHead("topic"),
      remotes: [createRemote("origin"), createRemote("fork")],
    });
    const harness = createHarness({
      repositories: [repository],
      remotePickIndex: null,
    });
    const integration = new GitIntegration(harness.vscode, harness.storage);

    const result = await integration.push({ id: 1 });

    assert.equal(result.status, "cancelled");
    assert.equal(harness.calls.warning.length, 0);
    assert.equal(repository.calls.push.length, 0);
  });
});

test("une association devenue obsolète est supprimée puis remplacée", async () => {
  const repository = createRepository("current", { working: ["ready.md"] });
  const storageValues = {
    [ASSOCIATIONS_STORAGE_KEY]: { "id:5": "file:///workspace/removed" },
  };
  const harness = createHarness({
    repositories: [repository],
    storageValues,
    warningResults: [COMMIT_CONFIRM_ACTION],
  });
  const integration = new GitIntegration(harness.vscode, harness.storage);

  const result = await integration.stageAndCommit({ id: 5, name: "Agent" });

  assert.equal(result.status, "committed");
  assert.equal(
    harness.storage.values[ASSOCIATIONS_STORAGE_KEY]["id:5"],
    repository.rootUri.toString(),
  );
  assert.ok(harness.calls.storageUpdates.length >= 2);
});

function createHarness({
  fileSelectionIndices = ALL_FILES,
  gitAvailable = true,
  gitInitiallyActive = true,
  inputResult = USE_SUGGESTION,
  onShowInputBox = undefined,
  quickPickIndex = 0,
  remotePickIndex = 0,
  repositories = [],
  storageValues = {},
  trusted = true,
  warningResults = [],
} = {}) {
  const calls = {
    errors: [],
    extensionActivate: 0,
    getExtension: 0,
    information: [],
    input: [],
    quickPick: [],
    storageUpdates: [],
    warning: [],
  };
  const pendingWarningResults = [...warningResults];
  const gitApi = createGitApi(repositories);
  const extensionExports = {
    getAPI: (version) => (version === 1 ? gitApi : undefined),
  };
  const extension = gitAvailable
    ? {
        isActive: gitInitiallyActive,
        exports: extensionExports,
        async activate() {
          calls.extensionActivate += 1;
          extension.isActive = true;
          return extensionExports;
        },
      }
    : undefined;
  const storage = {
    values: structuredClone(storageValues),
    get(key, fallback) {
      return Object.hasOwn(storage.values, key) ? storage.values[key] : fallback;
    },
    async update(key, value) {
      storage.values[key] = structuredClone(value);
      calls.storageUpdates.push({ key, value: structuredClone(value) });
    },
  };
  const vscode = {
    EventEmitter: FakeEventEmitter,
    extensions: {
      getExtension(identifier) {
        calls.getExtension += 1;
        assert.equal(identifier, "vscode.git");
        return extension;
      },
    },
    window: {
      async showErrorMessage(message) {
        calls.errors.push(message);
      },
      async showInformationMessage(message) {
        calls.information.push(message);
      },
      async showInputBox(options) {
        calls.input.push(options);
        if (onShowInputBox) {
          await onShowInputBox(options);
        }
        if (inputResult === USE_SUGGESTION) {
          return options.value;
        }
        return inputResult === CANCEL_INPUT ? undefined : inputResult;
      },
      async showQuickPick(items, options) {
        const kind = quickPickKind(items, options);
        calls.quickPick.push({ items, kind, options });
        if (kind === "changes") {
          if (fileSelectionIndices === null) {
            return undefined;
          }
          const indices = fileSelectionIndices === ALL_FILES
            ? items.map((_item, index) => index)
            : fileSelectionIndices;
          return indices.map((index) => items[index]).filter(Boolean);
        }
        if (kind === "remote") {
          return remotePickIndex === null ? undefined : items[remotePickIndex];
        }
        return quickPickIndex === null ? undefined : items[quickPickIndex];
      },
      async showWarningMessage(message, options, action) {
        calls.warning.push({ action, message, options });
        return pendingWarningResults.length > 0
          ? pendingWarningResults.shift()
          : action;
      },
    },
    workspace: { isTrusted: trusted },
  };

  return { calls, gitApi, storage, vscode };
}

function quickPickKind(items, options) {
  if (options && options.canPickMany) {
    return "changes";
  }
  if (items.every((item) => item && item.repository)) {
    return "repository";
  }
  if (items.every((item) => item && item.remote)) {
    return "remote";
  }
  return "unknown";
}

function createGitApi(repositories) {
  const openEmitter = new FakeEventEmitter();
  const closeEmitter = new FakeEventEmitter();
  return {
    repositories,
    onDidOpenRepository: openEmitter.event,
    onDidCloseRepository: closeEmitter.event,
    emitOpen: (repository) => openEmitter.fire(repository),
    emitClose: (repository) => closeEmitter.fire(repository),
  };
}

function createRepository(
  name,
  {
    working = [],
    staged = [],
    merge = [],
    pushError = undefined,
    head = createHead("main", { remote: "origin", name: "origin/main" }),
    remotes = [createRemote("origin")],
  } = {},
) {
  const changeEmitter = new FakeEventEmitter();
  const calls = { add: [], commit: [], push: [] };
  const rootUri = uri(`/workspace/${name}`);
  const makeChange = (value) => change(value, rootUri.path);
  return {
    rootUri,
    state: {
      HEAD: head,
      refs: [],
      remotes,
      submodules: [],
      rebaseCommit: undefined,
      mergeChanges: merge.map(makeChange),
      indexChanges: staged.map(makeChange),
      workingTreeChanges: working.map(makeChange),
      onDidChange: changeEmitter.event,
    },
    calls,
    makeChange,
    emitChange: () => changeEmitter.fire(undefined),
    async add(resources) {
      calls.add.push(resources);
    },
    async commit(message, options) {
      calls.commit.push({ message, options });
    },
    async push(...args) {
      calls.push.push(args);
      if (pushError) {
        throw new Error(pushError);
      }
    },
  };
}

function createHead(name, upstream = undefined) {
  return { name, upstream };
}

function createRemote(
  name,
  {
    fetchUrl = `https://example.test/${name}.git`,
    pushUrl = `https://example.test/${name}.git`,
    isReadOnly = false,
  } = {},
) {
  return { name, fetchUrl, pushUrl, isReadOnly };
}

function change(value, rootPath = "/workspace") {
  const path = value.startsWith("/") ? value : `${rootPath}/${value}`;
  return { uri: uri(path) };
}

function uri(path) {
  return {
    scheme: "file",
    authority: "",
    fsPath: path,
    path,
    toString() {
      return `file://${path}`;
    },
  };
}

class FakeEventEmitter {
  constructor() {
    this.listeners = new Set();
    this.event = (listener) => {
      this.listeners.add(listener);
      return {
        dispose: () => {
          this.listeners.delete(listener);
        },
      };
    };
  }

  fire(value) {
    for (const listener of [...this.listeners]) {
      listener(value);
    }
  }

  dispose() {
    this.listeners.clear();
  }
}

const ALL_FILES = Symbol("all-files");
const USE_SUGGESTION = Symbol("use-suggestion");
const CANCEL_INPUT = Symbol("cancel-input");
