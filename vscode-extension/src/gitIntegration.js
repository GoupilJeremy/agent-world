"use strict";

const GIT_EXTENSION_ID = "vscode.git";
const ASSOCIATIONS_STORAGE_KEY = "agentWorld.git.agentRepositories";
const COMMIT_CONFIRM_ACTION = "Indexer et valider";
const PUSH_CONFIRM_ACTION = "Pousser";
const MAX_SUGGESTED_MESSAGE_LENGTH = 72;
const MAX_COMMIT_MESSAGE_LENGTH = 120;

class GitIntegrationError extends Error {
  constructor(message) {
    super(message);
    this.name = "GitIntegrationError";
  }
}

/**
 * Adapter around VS Code's built-in Git extension API.
 *
 * The class deliberately never shells out to Git. All repository mutations go
 * through the API exported by the built-in `vscode.git` extension and require
 * an explicit user confirmation.
 */
class GitIntegration {
  constructor(
    vscode,
    storage,
    {
      gitExtensionId = GIT_EXTENSION_ID,
      storageKey = ASSOCIATIONS_STORAGE_KEY,
    } = {},
  ) {
    if (!vscode) {
      throw new TypeError("L'API VS Code est requise pour l'intégration Git.");
    }

    this.vscode = vscode;
    this.storage = storage || createMemoryStorage();
    this.gitExtensionId = gitExtensionId;
    this.storageKey = storageKey;
    this.gitApi = undefined;
    this.initialization = undefined;
    this.disposed = false;
    this.repositoryDisposables = new Map();
    this.apiDisposables = [];
    this.changeEmitter = new vscode.EventEmitter();
    this.onDidChangeRepository = this.changeEmitter.event;
  }

  /**
   * Eagerly discovers Git and starts watching repositories. Missing Git is not
   * fatal during extension activation; user-facing operations report it later.
   */
  async initialize() {
    try {
      await this._ensureGitApi();
      return true;
    } catch (_error) {
      return false;
    }
  }

  async linkAgentToRepository(agent) {
    return this._runUserAction(async () => {
      this._assertTrustedWorkspace();
      const agentIdentity = getAgentIdentity(agent);
      const repository = await this._selectRepository(agent, {
        forceSelection: true,
      });
      if (!repository) {
        return { status: "cancelled" };
      }

      await this.vscode.window.showInformationMessage(
        `L'agent ${agentIdentity.label} est lié au dépôt ${repositoryLabel(
          repository,
        )}.`,
      );
      return { status: "linked", repository };
    });
  }

  async getLinkedRepository(agent) {
    const agentIdentity = getAgentIdentity(agent);
    const repositories = await this._getRepositories();
    const associations = this._readAssociations();
    const linkedKey = associations[agentIdentity.key];

    if (!linkedKey) {
      return undefined;
    }

    const repository = repositories.find(
      (candidate) => repositoryKey(candidate) === linkedKey,
    );
    if (repository) {
      return repository;
    }

    delete associations[agentIdentity.key];
    await this.storage.update(this.storageKey, associations);
    return undefined;
  }

  async stageAndCommit(agent) {
    return this._runUserAction(async () => {
      this._assertTrustedWorkspace();
      const agentIdentity = getAgentIdentity(agent);
      const repository = await this._selectRepository(agent);
      if (!repository) {
        return { status: "cancelled" };
      }

      const summary = getChangeSummary(repository);
      if (summary.merge > 0) {
        throw new GitIntegrationError(
          "Résolvez les conflits Git avant de créer un commit.",
        );
      }
      if (summary.staged > 0) {
        throw new GitIntegrationError(
          "Désindexez les changements déjà préparés avant de créer un commit Agent World.",
        );
      }
      if (!summary.hasChanges) {
        await this.vscode.window.showInformationMessage(
          `Aucun changement à valider dans ${repositoryLabel(repository)}.`,
        );
        return { status: "no_changes", repository };
      }

      const selectedChanges = await this._selectChanges(repository);
      if (!selectedChanges || selectedChanges.length === 0) {
        return { status: "cancelled", repository };
      }
      const resources = selectedChanges.map((item) => item.resourcePath);

      const confirmation = await this.vscode.window.showWarningMessage(
        `Indexer et valider ${formatChangeCount(resources.length)} dans ${repositoryLabel(
          repository,
        )} ?`,
        { modal: true },
        COMMIT_CONFIRM_ACTION,
      );
      if (confirmation !== COMMIT_CONFIRM_ACTION) {
        return { status: "cancelled", repository };
      }

      const suggestion = suggestCommitMessage(agent, { total: resources.length });
      const enteredMessage = await this.vscode.window.showInputBox({
        title: "Agent World — Message de commit",
        prompt: `Commit pour ${agentIdentity.label}`,
        value: suggestion,
        ignoreFocusOut: true,
        validateInput: validateCommitMessage,
      });
      if (enteredMessage === undefined) {
        return { status: "cancelled", repository };
      }
      const message = normalizeCommitMessage(enteredMessage);

      if (getChangeSummary(repository).staged > 0) {
        throw new GitIntegrationError(
          "L'index Git a changé pendant l'opération ; aucun fichier Agent World n'a été indexé.",
        );
      }
      if (typeof repository.add !== "function") {
        throw new GitIntegrationError(
          "L'API Git ne permet pas d'indexer les changements de ce dépôt.",
        );
      }
      await repository.add(resources);

      if (typeof repository.commit !== "function") {
        throw new GitIntegrationError(
          "L'API Git ne permet pas de créer un commit dans ce dépôt.",
        );
      }
      await repository.commit(message, { postCommitCommand: null });
      await this.vscode.window.showInformationMessage(
        `Commit créé dans ${repositoryLabel(repository)}.`,
      );
      return {
        status: "committed",
        repository,
        message,
        staged: resources.length,
      };
    });
  }

  async push(agent) {
    return this._runUserAction(async () => {
      this._assertTrustedWorkspace();
      const repository = await this._selectRepository(agent);
      if (!repository) {
        return { status: "cancelled" };
      }

      const target = await this._resolvePushTarget(repository);
      if (!target) {
        return { status: "cancelled", repository };
      }
      const upstreamDetail = target.setUpstream
        ? " et configurer son upstream"
        : "";
      const confirmation = await this.vscode.window.showWarningMessage(
        `Pousser la branche « ${target.branchName} » vers « ${target.destination} »${upstreamDetail} ?`,
        { modal: true },
        PUSH_CONFIRM_ACTION,
      );
      if (confirmation !== PUSH_CONFIRM_ACTION) {
        return { status: "cancelled", repository };
      }

      if (typeof repository.push !== "function") {
        throw new GitIntegrationError(
          "L'API Git ne permet pas de pousser ce dépôt.",
        );
      }
      if (target.setUpstream) {
        await repository.push(target.remote.name, target.branchName, true);
      } else {
        await repository.push();
      }
      await this.vscode.window.showInformationMessage(
        `Branche ${target.branchName} poussée vers ${target.destination}.`,
      );
      return { status: "pushed", repository, ...target };
    });
  }

  async _selectChanges(repository) {
    const items = createChangeItems(repository);
    if (items.length === 0) {
      return [];
    }

    const selected = await this.vscode.window.showQuickPick(items, {
      title: "Agent World — Fichiers à indexer",
      placeHolder: "Sélectionnez explicitement les fichiers à inclure dans le commit",
      canPickMany: true,
      ignoreFocusOut: true,
      matchOnDescription: true,
    });
    return Array.isArray(selected) ? selected : undefined;
  }

  async _resolvePushTarget(repository) {
    const state = repository && repository.state ? repository.state : {};
    const head = state.HEAD;
    if (!head || !safeInlineText(head.name)) {
      throw new GitIntegrationError(
        "Une branche Git active est requise avant de pousser des commits.",
      );
    }

    const branchName = safeInlineText(head.name);
    const remotes = safeArray(state.remotes).filter(
      (remote) => remote && safeInlineText(remote.name) && remote.isReadOnly !== true,
    );
    if (remotes.length === 0) {
      throw new GitIntegrationError(
        "Aucun dépôt distant accessible en écriture n'est configuré.",
      );
    }

    if (head.upstream && safeInlineText(head.upstream.remote)) {
      const remoteName = safeInlineText(head.upstream.remote);
      const remote = remotes.find((candidate) => candidate.name === remoteName);
      if (!remote) {
        throw new GitIntegrationError(
          `Le dépôt distant upstream « ${remoteName} » est indisponible ou en lecture seule.`,
        );
      }
      return {
        remote,
        branchName,
        targetBranch: safeInlineText(head.upstream.name, branchName),
        destination: formatRemoteTarget(
          remote.name,
          safeInlineText(head.upstream.name, branchName),
        ),
        setUpstream: false,
      };
    }

    let remote;
    if (remotes.length === 1) {
      [remote] = remotes;
    } else {
      const selected = await this.vscode.window.showQuickPick(
        remotes.map((candidate) => ({
          label: candidate.name,
          description: safeInlineText(candidate.pushUrl, candidate.fetchUrl),
          remote: candidate,
        })),
        {
          title: "Agent World — Dépôt distant",
          placeHolder: `Choisissez où publier la branche ${branchName}`,
          matchOnDescription: true,
        },
      );
      if (!selected) {
        return undefined;
      }
      remote = selected.remote;
    }

    return {
      remote,
      branchName,
      targetBranch: branchName,
      destination: formatRemoteTarget(remote.name, branchName),
      setUpstream: true,
    };
  }

  async _runUserAction(action) {
    try {
      return await action();
    } catch (error) {
      const detail = errorMessage(error);
      try {
        await this.vscode.window.showErrorMessage(
          `Intégration Git Agent World : ${detail}`,
        );
      } catch (_notificationError) {
        // A notification failure must not create an unhandled command rejection.
      }
      return { status: "error", error };
    }
  }

  _assertTrustedWorkspace() {
    if (this.vscode.workspace.isTrusted !== true) {
      throw new GitIntegrationError(
        "Les opérations Git sont désactivées dans un workspace non approuvé.",
      );
    }
  }

  async _selectRepository(agent, { forceSelection = false } = {}) {
    const agentIdentity = getAgentIdentity(agent);
    if (!forceSelection) {
      const linked = await this.getLinkedRepository(agent);
      if (linked) {
        return linked;
      }
    }

    const repositories = await this._getRepositories();
    if (repositories.length === 0) {
      throw new GitIntegrationError(
        "Aucun dépôt Git n'est ouvert dans le workspace.",
      );
    }

    let repository;
    if (repositories.length === 1) {
      [repository] = repositories;
    } else {
      const items = repositories.map((candidate) => ({
        label: repositoryLabel(candidate),
        description: repositoryDescription(candidate),
        repository: candidate,
      }));
      const picked = await this.vscode.window.showQuickPick(items, {
        title: "Agent World — Dépôt Git",
        placeHolder: `Choisissez le dépôt à associer à ${agentIdentity.label}`,
        matchOnDescription: true,
      });
      if (!picked) {
        return undefined;
      }
      repository = picked.repository;
    }

    await this._saveAssociation(agentIdentity.key, repository);
    return repository;
  }

  async _saveAssociation(agentKey, repository) {
    const associations = this._readAssociations();
    associations[agentKey] = repositoryKey(repository);
    await this.storage.update(this.storageKey, associations);
  }

  _readAssociations() {
    const stored = this.storage.get(this.storageKey, {});
    if (!stored || typeof stored !== "object" || Array.isArray(stored)) {
      return {};
    }

    return Object.fromEntries(
      Object.entries(stored).filter(
        ([agentKey, repoKey]) =>
          typeof agentKey === "string" && typeof repoKey === "string",
      ),
    );
  }

  async _getRepositories() {
    const api = await this._ensureGitApi();
    return Array.isArray(api.repositories)
      ? api.repositories.filter(isRepository)
      : [];
  }

  async _ensureGitApi() {
    if (this.disposed) {
      throw new GitIntegrationError("L'intégration Git a été arrêtée.");
    }
    if (this.gitApi) {
      return this.gitApi;
    }
    if (!this.initialization) {
      this.initialization = this._loadGitApi().finally(() => {
        this.initialization = undefined;
      });
    }
    return this.initialization;
  }

  async _loadGitApi() {
    const extension = this.vscode.extensions.getExtension(this.gitExtensionId);
    if (!extension) {
      throw new GitIntegrationError(
        "L'extension Git intégrée de VS Code est indisponible.",
      );
    }

    let exportedApi = extension.exports;
    if (!extension.isActive) {
      exportedApi = (await extension.activate()) || extension.exports;
    }
    if (!exportedApi || typeof exportedApi.getAPI !== "function") {
      throw new GitIntegrationError(
        "L'extension Git intégrée n'expose pas une API compatible.",
      );
    }

    const api = exportedApi.getAPI(1);
    if (!api || !Array.isArray(api.repositories)) {
      throw new GitIntegrationError("L'API Git intégrée est invalide.");
    }
    if (this.disposed) {
      throw new GitIntegrationError("L'intégration Git a été arrêtée.");
    }

    this.gitApi = api;
    this._watchGitApi(api);
    return api;
  }

  _watchGitApi(api) {
    for (const repository of api.repositories) {
      this._watchRepository(repository);
    }

    if (typeof api.onDidOpenRepository === "function") {
      this.apiDisposables.push(
        api.onDidOpenRepository((repository) => {
          this._watchRepository(repository);
        }),
      );
    }
    if (typeof api.onDidCloseRepository === "function") {
      this.apiDisposables.push(
        api.onDidCloseRepository((repository) => {
          this._unwatchRepository(repository);
        }),
      );
    }
  }

  _watchRepository(repository) {
    let key;
    try {
      key = repositoryKey(repository);
    } catch (_error) {
      return;
    }
    if (
      this.disposed ||
      this.repositoryDisposables.has(key) ||
      !isRepository(repository) ||
      typeof repository.state.onDidChange !== "function"
    ) {
      return;
    }

    const disposable = repository.state.onDidChange(() => {
      if (this.disposed) {
        return;
      }
      this.changeEmitter.fire({
        repository,
        repositoryUri: repositoryKey(repository),
        summary: getChangeSummary(repository),
      });
    });
    this.repositoryDisposables.set(key, disposable);
  }

  _unwatchRepository(repository) {
    let key;
    try {
      key = repositoryKey(repository);
    } catch (_error) {
      return;
    }
    const disposable = this.repositoryDisposables.get(key);
    if (disposable && typeof disposable.dispose === "function") {
      disposable.dispose();
    }
    this.repositoryDisposables.delete(key);
  }

  dispose() {
    if (this.disposed) {
      return;
    }
    this.disposed = true;

    for (const disposable of this.repositoryDisposables.values()) {
      if (disposable && typeof disposable.dispose === "function") {
        disposable.dispose();
      }
    }
    this.repositoryDisposables.clear();
    for (const disposable of this.apiDisposables.splice(0)) {
      if (disposable && typeof disposable.dispose === "function") {
        disposable.dispose();
      }
    }
    this.changeEmitter.dispose();
    this.gitApi = undefined;
  }
}

function getChangeSummary(repository) {
  const state = repository && repository.state ? repository.state : {};
  const workingTree = safeArray(state.workingTreeChanges).length;
  const staged = safeArray(state.indexChanges).length;
  const merge = safeArray(state.mergeChanges).length;
  const total = workingTree + staged + merge;
  return {
    workingTree,
    staged,
    merge,
    total,
    hasChanges: total > 0,
  };
}

function collectUnstagedResources(repository) {
  return collectUnstagedEntries(repository).map(({ resourcePath }) => resourcePath);
}

function collectUnstagedEntries(repository) {
  const changes = safeArray(repository && repository.state?.workingTreeChanges);
  const entries = [];
  const seen = new Set();

  for (const change of changes) {
    const uri = change && change.uri;
    if (!uri) {
      continue;
    }
    const key = uriKey(uri);
    if (seen.has(key)) {
      continue;
    }
    seen.add(key);
    const resourcePath = uri.fsPath || uri.path;
    if (resourcePath) {
      entries.push({ change, resourcePath });
    }
  }
  return entries;
}

function createChangeItems(repository) {
  const rootPath = safeInlineText(repository && repository.rootUri?.path);
  return collectUnstagedEntries(repository).map(({ change, resourcePath }) => {
    const uriPath = safeInlineText(change.uri && change.uri.path);
    const relativePath = rootPath && uriPath.startsWith(`${rootPath}/`)
      ? uriPath.slice(rootPath.length + 1)
      : uriPath;
    return {
      label: relativePath || resourcePath,
      description: resourcePath,
      change,
      resourcePath,
    };
  });
}

function suggestCommitMessage(agent, summary = {}) {
  const label = safeInlineText(
    agent && typeof agent === "object" ? agent.name : undefined,
    "agent",
  );
  const total = Number.isFinite(Number(summary.total))
    ? Math.max(0, Math.round(Number(summary.total)))
    : 0;
  const subject = total === 1
    ? `chore: update ${label} output`
    : `chore: update ${label} outputs (${total} files)`;
  return truncateText(subject, MAX_SUGGESTED_MESSAGE_LENGTH);
}

function validateCommitMessage(value) {
  const message = safeInlineText(value);
  if (!message) {
    return "Le message de commit est requis.";
  }
  if (message.length > MAX_COMMIT_MESSAGE_LENGTH) {
    return `Le message doit contenir au plus ${MAX_COMMIT_MESSAGE_LENGTH} caractères.`;
  }
  return undefined;
}

function normalizeCommitMessage(value) {
  const message = safeInlineText(value);
  const validation = validateCommitMessage(message);
  if (validation) {
    throw new GitIntegrationError(validation);
  }
  return message;
}

function getAgentIdentity(agent) {
  if (agent && typeof agent === "object" && !Array.isArray(agent)) {
    const id = safeInlineText(agent.id);
    const name = safeInlineText(agent.name);
    if (id) {
      return { key: `id:${id}`, label: name || `#${id}` };
    }
    if (name) {
      return { key: `name:${name}`, label: name };
    }
  }

  const primitive = safeInlineText(agent);
  if (primitive) {
    return { key: `id:${primitive}`, label: `#${primitive}` };
  }
  throw new GitIntegrationError("Un agent est requis pour l'opération Git.");
}

function repositoryKey(repository) {
  if (!isRepository(repository)) {
    throw new GitIntegrationError("Le dépôt Git sélectionné est invalide.");
  }
  return uriKey(repository.rootUri);
}

function repositoryLabel(repository) {
  const rootUri = repository && repository.rootUri;
  const rawPath = safeInlineText(rootUri && (rootUri.fsPath || rootUri.path));
  const normalized = rawPath.replaceAll("\\", "/").replace(/\/$/, "");
  const label = normalized.split("/").pop();
  return label || "dépôt Git";
}

function repositoryDescription(repository) {
  const rootUri = repository && repository.rootUri;
  return safeInlineText(
    rootUri && (rootUri.fsPath || rootUri.path || uriKey(rootUri)),
  );
}

function isRepository(value) {
  return Boolean(value && value.rootUri && value.state);
}

function uriKey(uri) {
  if (uri && typeof uri.toString === "function") {
    return uri.toString();
  }
  if (uri && typeof uri === "object") {
    return `${uri.scheme || ""}://${uri.authority || ""}${uri.path || ""}`;
  }
  return String(uri || "");
}

function formatChangeCount(total) {
  return total === 1 ? "1 changement" : `${total} changements`;
}

function formatRemoteTarget(remoteName, branchName) {
  const normalizedRemote = safeInlineText(remoteName);
  const normalizedBranch = safeInlineText(branchName).replace(
    /^refs\/remotes\//,
    "",
  );
  return normalizedBranch.startsWith(`${normalizedRemote}/`)
    ? normalizedBranch
    : `${normalizedRemote}/${normalizedBranch}`;
}

function safeInlineText(value, fallback = "") {
  if (value === undefined || value === null) {
    return fallback;
  }
  const text = String(value)
    .replace(/[\u0000-\u001f\u007f]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
  return text || fallback;
}

function truncateText(value, maximumLength) {
  if (value.length <= maximumLength) {
    return value;
  }
  return `${value.slice(0, maximumLength - 1).trimEnd()}…`;
}

function safeArray(value) {
  return Array.isArray(value) ? value : [];
}

function errorMessage(error) {
  return error instanceof Error ? error.message : String(error || "Erreur inconnue");
}

function createMemoryStorage() {
  const values = new Map();
  return {
    get(key, fallback) {
      return values.has(key) ? values.get(key) : fallback;
    },
    async update(key, value) {
      values.set(key, value);
    },
  };
}

module.exports = {
  ASSOCIATIONS_STORAGE_KEY,
  COMMIT_CONFIRM_ACTION,
  GIT_EXTENSION_ID,
  GitIntegration,
  GitIntegrationError,
  MAX_COMMIT_MESSAGE_LENGTH,
  MAX_SUGGESTED_MESSAGE_LENGTH,
  PUSH_CONFIRM_ACTION,
  collectUnstagedResources,
  createChangeItems,
  getAgentIdentity,
  getChangeSummary,
  normalizeCommitMessage,
  repositoryKey,
  repositoryLabel,
  suggestCommitMessage,
  validateCommitMessage,
};
