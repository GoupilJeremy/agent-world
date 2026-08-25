"use strict";

const assert = require("node:assert/strict");
const { EventEmitter } = require("node:events");
const test = require("node:test");

const {
  AgentWorldApiClient,
  normalizeBaseUrl,
  requestJson,
} = require("../src/apiClient");

test("getAgents appelle GET /api/agents sur l’URL configurée", async () => {
  let capturedUrl;
  let capturedOptions;
  const expected = [{ id: 1, name: "Recherche" }];
  const client = new AgentWorldApiClient({
    baseUrl: "https://example.invalid:8443/base",
    timeoutMs: 1234,
    transport: async (url, options) => {
      capturedUrl = url;
      capturedOptions = options;
      return expected;
    },
  });

  const agents = await client.getAgents();

  assert.deepEqual(agents, expected);
  assert.equal(capturedUrl.href, "https://example.invalid:8443/base/api/agents");
  assert.deepEqual(capturedOptions, { timeoutMs: 1234 });
});

test("getAgents rejette une charge utile qui n’est pas une liste", async () => {
  const client = new AgentWorldApiClient({
    transport: async () => ({ agents: [] }),
  });

  await assert.rejects(client.getAgents(), /n’est pas une liste/);
});

test("getAgent encode l’identifiant et valide la réponse", async () => {
  let capturedUrl;
  const client = new AgentWorldApiClient({
    baseUrl: "https://example.invalid/prefix",
    transport: async (url) => {
      capturedUrl = url;
      return { id: "alpha/beta", name: "Agent" };
    },
  });

  const agent = await client.getAgent("alpha/beta");

  assert.equal(capturedUrl.pathname, "/prefix/api/agents/alpha%2Fbeta");
  assert.equal(agent.name, "Agent");
});

test("seules les URL HTTP et HTTPS sont acceptées", () => {
  assert.throws(() => normalizeBaseUrl("file:///tmp/agents"), /HTTP ou HTTPS/);
  assert.throws(() => normalizeBaseUrl("pas une url"), /invalide/);
  assert.equal(normalizeBaseUrl("http://localhost:5000").href, "http://localhost:5000/");
  assert.equal(
    normalizeBaseUrl("https://example.invalid/prefix").href,
    "https://example.invalid/prefix/",
  );
});

test("requestJson rejette un statut HTTP non réussi sans ouvrir de socket", async () => {
  const requestClient = createRequestClient({ statusCode: 503, body: "{}" });

  await assert.rejects(
    requestJson(new URL("http://example.invalid/api/agents"), { requestClient }),
    /statut 503/,
  );
});

test("requestJson rejette une réponse JSON invalide sans ouvrir de socket", async () => {
  const requestClient = createRequestClient({ statusCode: 200, body: "{invalide" });

  await assert.rejects(
    requestJson(new URL("http://example.invalid/api/agents"), { requestClient }),
    /JSON valide/,
  );
});

test("requestJson annule l’échéance globale après une réponse complète", async () => {
  const requestClient = createRequestClient({ body: '[{"id":1}]' });
  let clearedHandle;

  const payload = await requestJson(
    new URL("http://example.invalid/api/agents"),
    {
      requestClient,
      scheduleTimeout: () => "global-timeout",
      cancelTimeout: (handle) => {
        clearedHandle = handle;
      },
    },
  );

  assert.deepEqual(payload, [{ id: 1 }]);
  assert.equal(clearedHandle, "global-timeout");
});

test("requestJson interrompt une requête arrivée à expiration", async () => {
  const requestClient = createRequestClient({ neverRespond: true });
  let scheduledDelay;
  let clearedHandle;

  await assert.rejects(
    requestJson(new URL("http://example.invalid/api/agents"), {
      timeoutMs: 25,
      requestClient,
      scheduleTimeout: (callback, delay) => {
        scheduledDelay = delay;
        queueMicrotask(callback);
        return "global-timeout";
      },
      cancelTimeout: (handle) => {
        clearedHandle = handle;
      },
    }),
    /a expiré/,
  );

  assert.equal(scheduledDelay, 25);
  assert.equal(clearedHandle, "global-timeout");
  assert.equal(requestClient.lastRequest.destroyed, true);
});

function createRequestClient({ statusCode = 200, body = "[]", neverRespond = false }) {
  const client = {
    lastRequest: undefined,
    get(_url, _options, onResponse) {
      const request = new EventEmitter();
      request.destroyed = false;
      request.destroy = (error) => {
        request.destroyed = true;
        if (error) {
          queueMicrotask(() => request.emit("error", error));
        }
      };
      client.lastRequest = request;

      if (!neverRespond) {
        queueMicrotask(() => {
          const response = new EventEmitter();
          response.statusCode = statusCode;
          onResponse(response);
          response.emit("data", Buffer.from(body, "utf8"));
          response.emit("end");
        });
      }

      return request;
    },
  };
  return client;
}
