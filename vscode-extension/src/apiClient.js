"use strict";

const http = require("node:http");
const https = require("node:https");

const DEFAULT_BASE_URL = "http://127.0.0.1:5000";
const DEFAULT_TIMEOUT_MS = 5000;
const MAX_RESPONSE_BYTES = 5 * 1024 * 1024;

class AgentWorldApiClient {
  constructor({
    baseUrl = DEFAULT_BASE_URL,
    timeoutMs = DEFAULT_TIMEOUT_MS,
    transport = requestJson,
  } = {}) {
    this.baseUrl = normalizeBaseUrl(baseUrl);
    this.timeoutMs = normalizeTimeout(timeoutMs);
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

function normalizeTimeout(value) {
  const timeout = Number(value);
  if (!Number.isFinite(timeout) || timeout < 1) {
    return DEFAULT_TIMEOUT_MS;
  }
  return Math.round(timeout);
}

function requestJson(
  url,
  {
    timeoutMs = DEFAULT_TIMEOUT_MS,
    requestClient = undefined,
    scheduleTimeout = setTimeout,
    cancelTimeout = clearTimeout,
  } = {},
) {
  return new Promise((resolve, reject) => {
    const client = requestClient || (url.protocol === "https:" ? https : http);
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

      request = client.get(
        url,
        {
          headers: {
            Accept: "application/json",
            "User-Agent": "agent-world-vscode/0.2.0",
          },
        },
        (response) => {
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
              const body = Buffer.concat(chunks).toString("utf8");
              succeed(JSON.parse(body));
            } catch (_error) {
              fail(new Error("La réponse de l’API Agent World n’est pas du JSON valide."));
            }
          });
        },
      );
      request.on("error", fail);
    } catch (error) {
      fail(error);
    }
  });
}

module.exports = {
  AgentWorldApiClient,
  DEFAULT_BASE_URL,
  DEFAULT_TIMEOUT_MS,
  normalizeBaseUrl,
  requestJson,
};
