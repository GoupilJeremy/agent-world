"use strict";

const assert = require("node:assert/strict");
const path = require("node:path");
const test = require("node:test");
const { fileURLToPath } = require("node:url");

const {
  openGeneratedFile,
  validateWorkspaceFile,
} = require("../src/fileCommands");

test("les candidats relatifs, absolus internes et URI workspace restent soumis au picker", async (t) => {
  const cases = [
    {
      name: "chemin relatif",
      candidate: () => path.join("generated", "result.md"),
      expected: (harness) => path.join(harness.rootPaths[0], "generated", "result.md"),
    },
    {
      name: "chemin absolu interne",
      candidate: (harness) => path.join(harness.rootPaths[0], "result.md"),
      expected: (harness) => path.join(harness.rootPaths[0], "result.md"),
    },
    {
      name: "URI retournée par VS Code",
      candidate: (harness) => harness.vscode.Uri.file(
        path.join(harness.rootPaths[0], "result.md"),
      ),
      expected: (harness) => path.join(harness.rootPaths[0], "result.md"),
    },
  ];

  for (const currentCase of cases) {
    await t.test(currentCase.name, async () => {
      const harness = createHarness();
      const candidate = currentCase.candidate(harness);

      const result = await openGeneratedFile(
        harness.vscode,
        candidate,
        harness.dependencies,
      );

      assert.equal(result.status, "opened");
      assert.equal(harness.calls.showOpenDialog.length, 1, "le picker reste obligatoire");
      assert.equal(
        harness.calls.showOpenDialog[0].defaultUri.fsPath,
        path.resolve(currentCase.expected(harness)),
      );
      assert.equal(harness.calls.openTextDocument[0], result.uri);
    });
  }
});

test("les entrées dangereuses sont rejetées avant le picker", async (t) => {
  const cases = [
    { name: "vide", candidate: "", message: /vide/ },
    { name: "NUL", candidate: `result\0.md`, message: /NUL/ },
    { name: "traversal", candidate: "../secret.md", message: /traversée/ },
    {
      name: "traversal encodée",
      candidate: "%2e%2e/secret.md",
      message: /traversée/,
    },
    {
      name: "schéma hostile",
      candidate: "https://evil.invalid/result.md",
      message: /schéma/,
    },
    {
      name: "absolu externe",
      candidate: (harness) => path.join(path.dirname(harness.rootPaths[0]), "secret.md"),
      message: /racine du workspace/,
    },
  ];

  for (const currentCase of cases) {
    await t.test(currentCase.name, async () => {
      const harness = createHarness();
      const candidate =
        typeof currentCase.candidate === "function"
          ? currentCase.candidate(harness)
          : currentCase.candidate;

      const result = await openGeneratedFile(
        harness.vscode,
        candidate,
        harness.dependencies,
      );

      assert.equal(result.status, "error");
      assert.match(harness.calls.errors[0], currentCase.message);
      assert.equal(harness.calls.showOpenDialog.length, 0);
      assert.equal(harness.calls.openTextDocument.length, 0);
    });
  }
});

test("un candidat programmatique est refusé dans un workspace non approuvé", async () => {
  const harness = createHarness({ isTrusted: false });

  const result = await openGeneratedFile(
    harness.vscode,
    "result.md",
    harness.dependencies,
  );

  assert.equal(result.status, "error");
  assert.match(harness.calls.errors[0], /non approuvé/);
  assert.equal(harness.calls.showOpenDialog.length, 0);
});

test("l’annulation du picker de fichier ne tente aucune ouverture", async () => {
  const harness = createHarness({ pickerResult: null });

  const result = await openGeneratedFile(
    harness.vscode,
    "result.md",
    harness.dependencies,
  );

  assert.deepEqual(result, { status: "cancelled" });
  assert.equal(harness.calls.openTextDocument.length, 0);
  assert.equal(harness.calls.errors.length, 0);
});

test("la destination active ou beside est transmise à showTextDocument", async (t) => {
  for (const [location, expectedColumn] of [
    ["active", "active-column"],
    ["beside", "beside-column"],
  ]) {
    await t.test(location, async () => {
      const harness = createHarness({ location });

      const result = await openGeneratedFile(
        harness.vscode,
        "result.md",
        harness.dependencies,
      );

      assert.equal(result.status, "opened");
      assert.deepEqual(harness.calls.showTextDocument[0].options, {
        preview: false,
        viewColumn: expectedColumn,
      });
    });
  }
});

test("un relatif multi-root privilégie le workspace de l’éditeur actif", async () => {
  const harness = createHarness({ rootCount: 2, activeRootIndex: 1 });

  const result = await openGeneratedFile(
    harness.vscode,
    "generated/result.md",
    harness.dependencies,
  );

  assert.equal(result.status, "opened");
  assert.equal(
    harness.calls.showOpenDialog[0].defaultUri.fsPath,
    path.join(harness.rootPaths[1], "generated", "result.md"),
  );
  assert.equal(harness.calls.showWorkspaceFolderPick, 0);
});

test("un relatif multi-root demande une racine sans éditeur actif", async () => {
  const harness = createHarness({
    rootCount: 2,
    activeRootIndex: null,
    workspacePickIndex: 1,
  });

  const result = await openGeneratedFile(
    harness.vscode,
    "generated/result.md",
    harness.dependencies,
  );

  assert.equal(result.status, "opened");
  assert.equal(harness.calls.showWorkspaceFolderPick, 1);
  assert.equal(
    harness.calls.showOpenDialog[0].defaultUri.fsPath,
    path.join(harness.rootPaths[1], "generated", "result.md"),
  );
});

test("l’annulation du choix de workspace multi-root annule proprement", async () => {
  const harness = createHarness({
    rootCount: 2,
    activeRootIndex: null,
    workspacePickIndex: null,
  });

  const result = await openGeneratedFile(
    harness.vscode,
    "generated/result.md",
    harness.dependencies,
  );

  assert.deepEqual(result, { status: "cancelled" });
  assert.equal(harness.calls.showOpenDialog.length, 0);
  assert.equal(harness.calls.errors.length, 0);
});

test("workspace.fs.stat doit confirmer File avant l’ouverture", async () => {
  const harness = createHarness({ statType: 2 });

  const result = await openGeneratedFile(
    harness.vscode,
    "generated",
    harness.dependencies,
  );

  assert.equal(result.status, "error");
  assert.match(harness.calls.errors[0], /ne désigne pas un fichier/);
  assert.equal(harness.calls.openTextDocument.length, 0);
});

test("un lien symbolique local résolu hors workspace est rejeté", async () => {
  const harness = createHarness();
  const candidatePath = path.join(harness.rootPaths[0], "linked-result.md");
  harness.realpathOverrides.set(
    path.resolve(candidatePath),
    path.resolve(path.dirname(harness.rootPaths[0]), "outside", "result.md"),
  );

  const result = await openGeneratedFile(
    harness.vscode,
    candidatePath,
    harness.dependencies,
  );

  assert.equal(result.status, "error");
  assert.match(harness.calls.errors[0], /lien symbolique/);
  assert.equal(harness.calls.showOpenDialog.length, 0);
});

test("un fichier choisi manuellement hors workspace reste refusé", async () => {
  const harness = createHarness({ pickerResult: "external" });

  const result = await openGeneratedFile(
    harness.vscode,
    undefined,
    harness.dependencies,
  );

  assert.equal(result.status, "error");
  assert.match(harness.calls.errors[0], /racine du workspace/);
  assert.equal(harness.calls.openTextDocument.length, 0);
});

test("un workspace distant refuse un chemin programmatique qui n’est pas une URI VS Code", async () => {
  const rootUri = TestUri.remote("vscode-remote", "ssh-remote+demo", "/workspace");
  const fileUri = TestUri.remote(
    "vscode-remote",
    "ssh-remote+demo",
    "/workspace/result.md",
  );
  const folder = { index: 0, name: "remote", uri: rootUri };
  const vscode = {
    FileType: { File: 1, SymbolicLink: 64 },
    Uri: { isUri: (value) => value instanceof TestUri },
    workspace: {
      fs: { stat: async () => ({ type: 1 }) },
      getWorkspaceFolder: () => folder,
    },
  };

  await assert.rejects(
    validateWorkspaceFile(vscode, fileUri, [folder], {
      candidateKind: "relative",
      programmatic: true,
      realpath: async (value) => value,
    }),
    /URI fournie directement par VS Code/,
  );

  await assert.doesNotReject(
    validateWorkspaceFile(vscode, fileUri, [folder], {
      candidateKind: "uri",
      programmatic: true,
      realpath: async (value) => value,
    }),
  );
});

function createHarness({
  activeRootIndex = 0,
  isTrusted = true,
  location = "active",
  pickerResult = "default",
  rootCount = 1,
  statType = 1,
  workspacePickIndex = 0,
} = {}) {
  const fixtureBase = path.resolve("virtual-test-workspaces");
  const rootPaths = Array.from({ length: rootCount }, (_value, index) =>
    path.join(fixtureBase, `root-${index}`),
  );
  const folders = rootPaths.map((rootPath, index) => ({
    index,
    name: `root-${index}`,
    uri: TestUri.file(rootPath),
  }));
  const calls = {
    errors: [],
    openTextDocument: [],
    showOpenDialog: [],
    showTextDocument: [],
    showWorkspaceFolderPick: 0,
    stat: [],
  };
  const realpathOverrides = new Map();

  const vscode = {
    FileType: { File: 1, Directory: 2, SymbolicLink: 64 },
    Uri: {
      file: TestUri.file,
      isUri: (value) => value instanceof TestUri,
      joinPath: (baseUri, ...segments) =>
        baseUri.scheme === "file"
          ? TestUri.file(path.join(baseUri.fsPath, ...segments))
          : TestUri.remote(
              baseUri.scheme,
              baseUri.authority,
              path.posix.join(baseUri.path, ...segments),
            ),
      parse: (value) => TestUri.parse(value),
    },
    ViewColumn: { Active: "active-column", Beside: "beside-column" },
    window: {
      activeTextEditor:
        activeRootIndex === null
          ? undefined
          : {
              document: {
                uri: TestUri.file(path.join(rootPaths[activeRootIndex], "active.md")),
              },
            },
      showErrorMessage: async (message) => {
        calls.errors.push(message);
      },
      showOpenDialog: async (options) => {
        calls.showOpenDialog.push(options);
        if (pickerResult === null) {
          return undefined;
        }
        if (pickerResult === "external") {
          return [TestUri.file(path.join(fixtureBase, "outside", "result.md"))];
        }
        if (pickerResult instanceof TestUri) {
          return [pickerResult];
        }
        return [
          options.defaultUri || TestUri.file(path.join(rootPaths[0], "selected.md")),
        ];
      },
      showTextDocument: async (document, options) => {
        calls.showTextDocument.push({ document, options });
      },
      showWorkspaceFolderPick: async () => {
        calls.showWorkspaceFolderPick += 1;
        return workspacePickIndex === null ? undefined : folders[workspacePickIndex];
      },
    },
    workspace: {
      fs: {
        stat: async (uri) => {
          calls.stat.push(uri);
          return { type: statType };
        },
      },
      getConfiguration: () => ({
        get: (key, fallback) =>
          key === "openFile.location" ? location : fallback,
      }),
      getWorkspaceFolder: (uri) =>
        [...folders]
          .sort((left, right) => right.uri.fsPath.length - left.uri.fsPath.length)
          .find((folder) => isPathInside(uri.fsPath, folder.uri.fsPath)),
      isTrusted,
      openTextDocument: async (uri) => {
        calls.openTextDocument.push(uri);
        return { uri };
      },
      workspaceFolders: folders,
    },
  };

  return {
    calls,
    dependencies: {
      realpath: async (value) =>
        realpathOverrides.get(path.resolve(value)) || path.resolve(value),
    },
    realpathOverrides,
    rootPaths,
    vscode,
  };
}

function isPathInside(candidatePath, rootPath) {
  const relative = path.relative(path.resolve(rootPath), path.resolve(candidatePath));
  return (
    relative === "" ||
    (relative !== ".." &&
      !relative.startsWith(`..${path.sep}`) &&
      !path.isAbsolute(relative))
  );
}

class TestUri {
  constructor({ authority = "", fsPath = "", pathValue, scheme }) {
    this.authority = authority;
    this.fsPath = fsPath;
    this.path = pathValue;
    this.scheme = scheme;
  }

  static file(value) {
    const fsPath = path.resolve(value);
    return new TestUri({
      fsPath,
      pathValue: fsPath.replaceAll(path.sep, "/"),
      scheme: "file",
    });
  }

  static parse(value) {
    const parsed = new URL(value);
    if (parsed.protocol === "file:") {
      return TestUri.file(fileURLToPath(parsed));
    }
    return TestUri.remote(
      parsed.protocol.slice(0, -1),
      parsed.host,
      decodeURIComponent(parsed.pathname),
    );
  }

  static remote(scheme, authority, pathValue) {
    return new TestUri({ authority, pathValue, scheme });
  }
}
