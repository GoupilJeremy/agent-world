"use strict";

const fs = require("node:fs/promises");
const path = require("node:path");

const HOSTILE_SCHEMES = new Set([
  "command",
  "data",
  "http",
  "https",
  "javascript",
  "untitled",
]);

async function openGeneratedFile(vscode, candidate, dependencies = {}) {
  const hasCandidate = candidate !== undefined && candidate !== null;
  const realpath = dependencies.realpath || fs.realpath;

  try {
    const workspaceFolders = getWorkspaceFolders(vscode);
    if (workspaceFolders.length === 0) {
      throw new Error("Ouvrez d’abord un dossier de travail dans VS Code.");
    }

    let defaultUri;
    if (hasCandidate) {
      if (vscode.workspace.isTrusted !== true) {
        throw new Error(
          "L’ouverture programmatique est désactivée dans un workspace non approuvé.",
        );
      }

      const resolved = await resolveCandidate(vscode, candidate, workspaceFolders);
      if (!resolved) {
        return { status: "cancelled" };
      }

      await validateWorkspaceFile(vscode, resolved.uri, workspaceFolders, {
        candidateKind: resolved.kind,
        programmatic: true,
        realpath,
      });
      defaultUri = resolved.uri;
    }

    const pickerOptions = {
      canSelectFiles: true,
      canSelectFolders: false,
      canSelectMany: false,
      openLabel: "Ouvrir le fichier généré",
      title: "Agent World — Ouvrir un fichier généré",
    };
    if (defaultUri) {
      pickerOptions.defaultUri = defaultUri;
    }

    const selectedUris = await vscode.window.showOpenDialog(pickerOptions);
    if (!selectedUris || selectedUris.length === 0) {
      return { status: "cancelled" };
    }

    const selectedUri = selectedUris[0];
    await validateWorkspaceFile(vscode, selectedUri, workspaceFolders, {
      candidateKind: "picker",
      programmatic: false,
      realpath,
    });

    const document = await vscode.workspace.openTextDocument(selectedUri);
    const location = vscode.workspace
      .getConfiguration("agentWorld")
      .get("openFile.location", "active");
    const viewColumn =
      location === "beside" ? vscode.ViewColumn.Beside : vscode.ViewColumn.Active;
    await vscode.window.showTextDocument(document, {
      preview: false,
      viewColumn,
    });
    return { status: "opened", uri: selectedUri };
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error || "Erreur inconnue");
    await vscode.window.showErrorMessage(
      `Impossible d’ouvrir le fichier généré : ${detail}`,
    );
    return { status: "error", error };
  }
}

async function resolveCandidate(vscode, candidate, workspaceFolders) {
  if (isUri(vscode, candidate)) {
    assertSafeUri(candidate);
    return { uri: candidate, kind: "uri" };
  }

  if (typeof candidate !== "string") {
    throw new Error("Le chemin de fichier fourni est invalide.");
  }

  assertSafeRawPath(candidate);

  if (looksLikeUri(candidate) && !looksLikeWindowsAbsolutePath(candidate)) {
    const uri = vscode.Uri.parse(candidate, true);
    assertSafeUri(uri);
    return { uri, kind: "uri-string" };
  }

  if (isAbsolutePath(candidate)) {
    const uri = vscode.Uri.file(candidate);
    assertSafeUri(uri);
    return { uri, kind: "absolute" };
  }

  assertNoTraversal(candidate);
  const workspaceFolder = await chooseWorkspaceFolder(vscode, workspaceFolders);
  if (!workspaceFolder) {
    return undefined;
  }

  const segments = candidate
    .replaceAll("\\", "/")
    .split("/")
    .filter((segment) => segment && segment !== ".");
  if (segments.length === 0) {
    throw new Error("Le chemin de fichier fourni est vide.");
  }

  return {
    uri: vscode.Uri.joinPath(workspaceFolder.uri, ...segments),
    kind: "relative",
  };
}

async function chooseWorkspaceFolder(vscode, workspaceFolders) {
  if (workspaceFolders.length === 1) {
    return workspaceFolders[0];
  }

  const activeUri = vscode.window.activeTextEditor?.document?.uri;
  if (activeUri) {
    const activeFolder = findContainingWorkspaceFolder(
      vscode,
      activeUri,
      workspaceFolders,
    );
    if (activeFolder) {
      return activeFolder;
    }
  }

  return vscode.window.showWorkspaceFolderPick({
    placeHolder: "Choisissez le dossier contenant le fichier généré",
  });
}

async function validateWorkspaceFile(
  vscode,
  uri,
  workspaceFolders,
  { candidateKind, programmatic, realpath },
) {
  if (!isUri(vscode, uri)) {
    throw new Error("Le sélecteur n’a pas retourné une URI de fichier valide.");
  }
  assertSafeUri(uri);

  const workspaceFolder = findContainingWorkspaceFolder(
    vscode,
    uri,
    workspaceFolders,
  );
  if (!workspaceFolder || !isUriInside(uri, workspaceFolder.uri)) {
    throw new Error("Le fichier doit rester dans une racine du workspace.");
  }

  const stat = await vscode.workspace.fs.stat(uri);
  const fileType = vscode.FileType.File;
  if ((stat.type & fileType) !== fileType) {
    throw new Error("L’URI sélectionnée ne désigne pas un fichier.");
  }

  if (uri.scheme.toLowerCase() === "file") {
    const [canonicalRoot, canonicalFile] = await Promise.all([
      realpath(workspaceFolder.uri.fsPath),
      realpath(uri.fsPath),
    ]);
    if (!isFileSystemPathInside(canonicalFile, canonicalRoot)) {
      throw new Error(
        "Le chemin résolu sort de la racine du workspace (lien symbolique refusé).",
      );
    }
  } else if (programmatic) {
    if (candidateKind !== "uri") {
      throw new Error(
        "Un workspace distant exige une URI fournie directement par VS Code.",
      );
    }
    const symbolicLink = vscode.FileType.SymbolicLink || 64;
    if ((stat.type & symbolicLink) === symbolicLink) {
      throw new Error(
        "Les liens symboliques distants ne sont pas ouverts programmatiquement.",
      );
    }
  }

  return workspaceFolder;
}

function findContainingWorkspaceFolder(vscode, uri, workspaceFolders) {
  const direct = vscode.workspace.getWorkspaceFolder(uri);
  if (direct && workspaceFolders.some((folder) => sameUri(folder.uri, direct.uri))) {
    return direct;
  }

  return [...workspaceFolders]
    .sort((left, right) => right.uri.path.length - left.uri.path.length)
    .find((folder) => isUriInside(uri, folder.uri));
}

function isUriInside(uri, rootUri) {
  if (
    uri.scheme.toLowerCase() !== rootUri.scheme.toLowerCase() ||
    String(uri.authority || "").toLowerCase() !==
      String(rootUri.authority || "").toLowerCase()
  ) {
    return false;
  }

  if (uri.scheme.toLowerCase() === "file") {
    return isFileSystemPathInside(uri.fsPath, rootUri.fsPath);
  }

  const relative = path.posix.relative(
    path.posix.normalize(rootUri.path),
    path.posix.normalize(uri.path),
  );
  return isSafeRelativeResult(relative, path.posix);
}

function isFileSystemPathInside(candidatePath, rootPath) {
  const relative = path.relative(path.resolve(rootPath), path.resolve(candidatePath));
  return isSafeRelativeResult(relative, path);
}

function isSafeRelativeResult(relative, pathModule) {
  return (
    relative === "" ||
    (relative !== ".." &&
      !relative.startsWith(`..${pathModule.sep}`) &&
      !pathModule.isAbsolute(relative))
  );
}

function getWorkspaceFolders(vscode) {
  return Array.isArray(vscode.workspace.workspaceFolders)
    ? vscode.workspace.workspaceFolders
    : [];
}

function isUri(vscode, value) {
  if (vscode.Uri && typeof vscode.Uri.isUri === "function") {
    return vscode.Uri.isUri(value);
  }
  return Boolean(
    value &&
      typeof value === "object" &&
      typeof value.scheme === "string" &&
      typeof value.path === "string",
  );
}

function assertSafeUri(uri) {
  const scheme = String(uri.scheme || "").toLowerCase();
  if (!scheme || HOSTILE_SCHEMES.has(scheme)) {
    throw new Error(`Le schéma d’URI « ${scheme || "vide"} » est refusé.`);
  }
  assertSafeRawPath(String(uri.path || ""));
  assertNoTraversal(String(uri.path || ""));
}

function assertSafeRawPath(value) {
  if (value.trim() === "") {
    throw new Error("Le chemin de fichier fourni est vide.");
  }
  if (value.includes("\0")) {
    throw new Error("Le chemin de fichier contient un caractère NUL interdit.");
  }

  let decoded;
  try {
    decoded = decodeURIComponent(value);
  } catch (_error) {
    throw new Error("Le chemin de fichier contient un encodage invalide.");
  }
  if (decoded.includes("\0")) {
    throw new Error("Le chemin de fichier contient un caractère NUL interdit.");
  }
}

function assertNoTraversal(value) {
  let decoded = value;
  try {
    decoded = decodeURIComponent(value);
  } catch (_error) {
    throw new Error("Le chemin de fichier contient un encodage invalide.");
  }
  if (decoded.replaceAll("\\", "/").split("/").includes("..")) {
    throw new Error("La traversée de dossiers avec « .. » est interdite.");
  }
}

function looksLikeUri(value) {
  return /^[A-Za-z][A-Za-z\d+.-]*:/.test(value);
}

function looksLikeWindowsAbsolutePath(value) {
  return /^[A-Za-z]:[\\/]/.test(value) || /^\\\\/.test(value);
}

function isAbsolutePath(value) {
  return (
    path.isAbsolute(value) ||
    path.win32.isAbsolute(value) ||
    path.posix.isAbsolute(value)
  );
}

function sameUri(left, right) {
  return (
    left.scheme.toLowerCase() === right.scheme.toLowerCase() &&
    String(left.authority || "").toLowerCase() ===
      String(right.authority || "").toLowerCase() &&
    left.path === right.path
  );
}

module.exports = {
  assertNoTraversal,
  findContainingWorkspaceFolder,
  isFileSystemPathInside,
  isUriInside,
  openGeneratedFile,
  resolveCandidate,
  validateWorkspaceFile,
};
