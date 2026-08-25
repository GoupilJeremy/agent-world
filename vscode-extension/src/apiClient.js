"use strict";

const http = require("node:http");
const https = require("node:https");

const DEFAULT_BASE_URL = "http://127.0.0.1:5000";
const DEFAULT_TIMEOUT_MS = 5000;
const DEFAULT_EXECUTION_TIMEOUT_MS = 120000;
const MAX_REQUEST_BYTES = 1024 * 1024;
const MAX_RESPONSE_BYTES = 5 * 1024 * 1024;

class AgentWorldApiClient {
  constructor({
    baseUrl = DEFAULT_BASE_URL,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    executionTimeoutMs = DEFAULT_EXECUTION_TIMEOUT_MS,
    transport = requestJson,
  } = {}) {
    this.baseUrl = normalizeBaseUrl(baseUrl);
    this.timeoutMs = normalizeTimeout(timeoutMs);
    this.executionTimeoutMs = normalizeTimeout(
      executionTimeoutMs,
      DEFAULT_EXECUTION_TIMEOUT_MS,
    );
    this.transport = transport;
  }

  async getAgents() {
    const url = new URL("api/agents", this.baseUrl);
    const payload = await this.transport(url, { timeoutMs: this.timeoutMs });

    if (!Array.isArray(payload)) {
      throw new Error("La réponse de l’API pour les agents n’est pas une liste.");
    }

    return payload;
  }

  async getAgent(agentId) {
    if (agentId === undefined || agentId === null || String(agentId).trim() === "") {
      throw new Error("Un identifiant d’agent est requis.");
    }

    const encodedId = encodeURIComponent(String(agentId));
    const url = new URL(`api/agents/${encodedId}`, this.baseUrl);
    const payload = await this.transport(url, { timeoutMs: this.timeoutMs });

    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error("La réponse de l’API pour cet agent est invalide.");
    }

    return payload;
  }

  async runAgent(agentId, input, options = {}) {
    if (agentId === undefined || agentId === null || String(agentId).trim() === "") {
      throw new Error("Un identifiant d’agent est requis.");
    }
    if (typeof input !== "string" || input.trim() === "") {
      throw new Error("Une entrée non vide est requise pour exécuter l’agent.");
    }
    if (!options || typeof options !== "object" || Array.isArray(options)) {
      throw new Error("Les options d’exécution de l’agent sont invalides.");
    }

    const body = { input };
    if (options.model !== undefined) {
      if (typeof options.model !== "string" || options.model.trim() === "") {
        throw new Error("Le modèle de l’agent doit être une chaîne non vide.");
      }
      body.model = options.model;
    }
    if (options.configuration !== undefined) {
      if (
        !options.configuration ||
        typeof options.configuration !== "object" ||
        Array.isArray(options.configuration)
      ) {
        throw new Error("La configuration de l’agent doit être un objet JSON.");
      }
      body.configuration = options.configuration;
    }

    const encodedId = encodeURIComponent(String(agentId));
    const url = new URL(`api/agents/${encodedId}/run`, this.baseUrl);
    const payload = await this.transport(url, {
      method: "POST",
      body,
      timeoutMs: this.executionTimeoutMs,
    });

    if (!payload || typeof payload !== "object" || Array.isArray(payload)) {
      throw new Error("La réponse de l’API pour cette exécution est invalide.");
    }
    if (
      payload.execution_id === undefined ||
      payload.execution_id === null ||
      String(payload.execution_id).trim() === "" ||
      payload.agent_id === undefined ||
      payload.agent_id === null ||
      typeof payload.status !== "string" ||
      payload.status.trim() === ""
    ) {
      throw new Error("La réponse de l’API pour cette exécution est incomplète.");
    }
    if (String(payload.agent_id) !== String(agentId)) {
      throw new Error("La réponse de l’API concerne un autre agent.");
    }

    return payload;
  }
}

function normalizeBaseUrl(value) {
  let parsed;

  try {
    parsed = new URL(String(value || DEFAULT_BASE_URL));
  } catch (_error) {
    throw new Error("L’URL de l’API Agent World est invalide.");
  }

  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
    throw new Error("L’URL de l’API doit utiliser HTTP ou HTTPS.");
  }

  parsed.username = "";
  parsed.password = "";
  parsed.hash = "";
  parsed.search = "";
  if (!parsed.pathname.endsWith("/")) {
    parsed.pathname = `${parsed.pathname}/`;
  }
  return parsed;
}

function normalizeTimeout(value, fallback = DEFAULT_TIMEOUT_MS) {
  const timeout = Number(value);
  if (!Number.isFinite(timeout) || timeout < 1) {
    return fallback;
  }
  return Math.round(timeout);
}

function requestJson(
  url,
  {
    method = "GET",
    body = undefined,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    requestClient = undefined,
    scheduleTimeout = setTimeout,
    cancelTimeout = clearTimeout,
  } = {},
) {
  return new Promise((resolve, reject) => {
    const client = requestClient || (url.protocol === "https:" ? https : http);
    let normalizedMethod;
    let requestBody;

    try {
      normalizedMethod = String(method).toUpperCase();
      if (normalizedMethod !== "GET" && normalizedMethod !== "POST") {
        throw new Error("La méthode HTTP demandée n’est pas autorisée.");
      }
      if (normalizedMethod === "GET" && body !== undefined) {
        throw new Error("Une requête GET ne peut pas contenir de corps JSON.");
      }
      if (body !== undefined) {
        const serializedBody = JSON.stringify(body);
        if (serializedBody === undefined) {
          throw new Error("Le corps de la requête n’est pas sérialisable en JSON.");
        }
        requestBody = Buffer.from(serializedBody, "utf8");
        if (requestBody.length > MAX_REQUEST_BYTES) {
          throw new Error("Le corps JSON de la requête est trop volumineux.");
        }
      }
    } catch (error) {
      reject(
        error instanceof Error
          ? error
          : new Error("Le corps de la requête n’est pas sérialisable en JSON."),
      );
      return;
    }

    let request;
    let timeoutHandle;
    let settled = false;

    const cleanup = () => {
      if (timeoutHandle !== undefined) {
        cancelTimeout(timeoutHandle);
        timeoutHandle = undefined;
      }
    };
    const succeed = (value) => {
      if (settled) {
        return;
      }
      settled = true;
      cleanup();
      resolve(value);
    };
    const fail = (error) => {
      if (settled) {
        return false;
      }
      settled = true;
      cleanup();
      reject(error);
      return true;
    };

    try {
      timeoutHandle = scheduleTimeout(() => {
        const didFail = fail(
          new Error("La requête vers l’API Agent World a expiré."),
        );
        if (didFail && request && !request.destroyed) {
          request.destroy();
        }
      }, normalizeTimeout(timeoutMs));

      if (settled) {
        cleanup();
        return;
      }

      const headers = {
        Accept: "application/json",
        "User-Agent": "agent-world-vscode/0.2.0",
      };
      if (requestBody !== undefined) {
        headers["Content-Type"] = "application/json; charset=utf-8";
        headers["Content-Length"] = requestBody.length;
      }
      const requestOptions = { headers };
      const onResponse = (response) => {
        const chunks = [];
        let receivedBytes = 0;

        response.on("error", fail);
        response.on("data", (chunk) => {
          if (settled) {
            return;
          }
          receivedBytes += chunk.length;
          if (receivedBytes > MAX_RESPONSE_BYTES) {
            const didFail = fail(
              new Error("La réponse de l’API Agent World est trop volumineuse."),
            );
            if (didFail && request && !request.destroyed) {
              request.destroy();
            }
            return;
          }
          chunks.push(chunk);
        });

        response.on("end", () => {
          if (settled) {
            return;
          }
          if (response.statusCode < 200 || response.statusCode >= 300) {
            fail(
              new Error(
                `L’API Agent World a répondu avec le statut ${response.statusCode}.`,
              ),
            );
            return;
          }

          try {
            const responseBody = Buffer.concat(chunks).toString("utf8");
            succeed(JSON.parse(responseBody));
          } catch (_error) {
            fail(
              new Error(
                "La réponse de l’API Agent World n’est pas du JSON valide.",
              ),
            );
          }
        });
      };

      if (normalizedMethod === "GET") {
        request = client.get(url, requestOptions, onResponse);
      } else {
        request = client.request(
          url,
          { ...requestOptions, method: normalizedMethod },
          onResponse,
        );
      }
      request.on("error", fail);
      if (normalizedMethod === "POST") {
        if (requestBody !== undefined) {
          request.write(requestBody);
        }
        request.end();
      }
    } catch (error) {
      const didFail = fail(error);
      if (didFail && request && !request.destroyed) {
        request.destroy();
      }
    }
  });
}

module.exports = {
  AgentWorldApiClient,
  DEFAULT_BASE_URL,
  DEFAULT_EXECUTION_TIMEOUT_MS,
  DEFAULT_TIMEOUT_MS,
  MAX_REQUEST_BYTES,
  normalizeBaseUrl,
  requestJson,
};
