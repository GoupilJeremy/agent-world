"use strict";

const assert = require("node:assert/strict");
const { EventEmitter } = require("node:events");
const test = require("node:test");

const {
  AgentWorldApiClient,
  MAX_REQUEST_BYTES,
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

test("runAgent envoie un POST JSON avec les options et le timeout configures", async () => {
  let capturedUrl;
  let capturedOptions;
  const expected = {
    execution_id: 12,
    agent_id: "alpha/beta",
    status: "completed",
  };
  const client = new AgentWorldApiClient({
    baseUrl: "https://example.invalid/prefix",
    timeoutMs: 2345,
    executionTimeoutMs: 120000,
    transport: async (url, options) => {
      capturedUrl = url;
      capturedOptions = options;
      return expected;
    },
  });

  const execution = await client.runAgent("alpha/beta", "Analyse ce fichier", {
    model: "gpt-4",
    configuration: { temperature: 0.2 },
  });

  assert.deepEqual(execution, expected);
  assert.equal(capturedUrl.pathname, "/prefix/api/agents/alpha%2Fbeta/run");
  assert.deepEqual(capturedOptions, {
    method: "POST",
    body: {
      input: "Analyse ce fichier",
      model: "gpt-4",
      configuration: { temperature: 0.2 },
    },
    timeoutMs: 120000,
  });
});

test("runAgent utilise un timeout d'exécution distinct des lectures", async () => {
  const capturedTimeouts = [];
  const client = new AgentWorldApiClient({
    timeoutMs: 3210,
    executionTimeoutMs: 6543,
    transport: async (_url, options) => {
      capturedTimeouts.push(options.timeoutMs);
      return capturedTimeouts.length === 1
        ? []
        : { execution_id: 1, agent_id: 7, status: "completed" };
    },
  });

  await client.getAgents();
  await client.runAgent(7, "Tester");

  assert.deepEqual(capturedTimeouts, [3210, 6543]);
});

test("runAgent valide les donnees avant tout appel reseau", async () => {
  let calls = 0;
  const client = new AgentWorldApiClient({
    transport: async () => {
      calls += 1;
      return {};
    },
  });

  await assert.rejects(client.runAgent(undefined, "input"), /identifiant/);
  await assert.rejects(client.runAgent(1, "  "), /entrée non vide/);
  await assert.rejects(
    client.runAgent(1, "input", { configuration: [] }),
    /configuration/,
  );
  assert.equal(calls, 0);
});

test("runAgent rejette un contrat d’exécution incomplet ou incohérent", async () => {
  const incomplete = new AgentWorldApiClient({
    transport: async () => ({ status: "completed" }),
  });
  const wrongAgent = new AgentWorldApiClient({
    transport: async () => ({
      execution_id: 1,
      agent_id: 99,
      status: "completed",
    }),
  });

  await assert.rejects(incomplete.runAgent(1, "input"), /incomplète/);
  await assert.rejects(wrongAgent.runAgent(1, "input"), /autre agent/);
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

test("requestJson ecrit un POST JSON avec des en-tetes bornes", async () => {
  const requestClient = createRequestClient({
    body: '{"status":"completed"}',
  });
  const requestBody = { input: "Bonjour", configuration: { temperature: 0.3 } };

  const payload = await requestJson(
    new URL("http://example.invalid/api/agents/1/run"),
    {
      method: "POST",
      body: requestBody,
      requestClient,
    },
  );

  const serialized = JSON.stringify(requestBody);
  assert.deepEqual(payload, { status: "completed" });
  assert.equal(requestClient.lastOptions.method, "POST");
  assert.equal(
    requestClient.lastOptions.headers["Content-Type"],
    "application/json; charset=utf-8",
  );
  assert.equal(
    requestClient.lastOptions.headers["Content-Length"],
    Buffer.byteLength(serialized),
  );
  assert.equal(requestClient.lastRequest.body.toString("utf8"), serialized);
  assert.equal(requestClient.lastRequest.ended, true);
});

test("requestJson refuse les methodes et corps JSON dangereux", async () => {
  const requestClient = createRequestClient({});
  const url = new URL("http://example.invalid/api/agents/1/run");

  await assert.rejects(
    requestJson(url, { method: "DELETE", requestClient }),
    /méthode HTTP/,
  );
  await assert.rejects(
    requestJson(url, { method: "GET", body: {}, requestClient }),
    /requête GET/,
  );
  await assert.rejects(
    requestJson(url, {
      method: "POST",
      body: { input: "x".repeat(MAX_REQUEST_BYTES) },
      requestClient,
    }),
    /trop volumineux/,
  );
  assert.equal(requestClient.lastRequest, undefined);
});

function createRequestClient({ statusCode = 200, body = "[]", neverRespond = false }) {
  const emitResponse = (request, onResponse) => {
    if (neverRespond || request.destroyed || request.responseScheduled) {
      return;
    }
    request.responseScheduled = true;
    queueMicrotask(() => {
      if (request.destroyed) {
        return;
      }
      const response = new EventEmitter();
      response.statusCode = statusCode;
      onResponse(response);
      response.emit("data", Buffer.from(body, "utf8"));
      response.emit("end");
    });
  };
  const createRequest = (options, onResponse, autoEnd) => {
    const request = new EventEmitter();
    request.body = Buffer.alloc(0);
    request.destroyed = false;
    request.ended = autoEnd;
    request.responseScheduled = false;
    request.destroy = (error) => {
      request.destroyed = true;
      if (error) {
        queueMicrotask(() => request.emit("error", error));
      }
    };
    request.write = (chunk) => {
      request.body = Buffer.concat([request.body, Buffer.from(chunk)]);
      return true;
    };
    request.end = () => {
      request.ended = true;
      emitResponse(request, onResponse);
    };
    client.lastOptions = options;
    client.lastRequest = request;

    if (autoEnd) {
      emitResponse(request, onResponse);
    }
    return request;
  };
  const client = {
    lastRequest: undefined,
    lastOptions: undefined,
    get(_url, options, onResponse) {
      return createRequest(options, onResponse, true);
    },
    request(_url, options, onResponse) {
      return createRequest(options, onResponse, false);
    },
  };
  return client;
}
