"use strict";

const assert = require("node:assert/strict");
const test = require("node:test");

const { withSelectedAgent } = require("../src/gitCommand");

test("une commande Git sans candidat ne consulte pas l'API hors workspace approuvé", async () => {
  let clientCalls = 0;
  let actionCalls = 0;
  const errors = [];
  const vscode = {
    workspace: { isTrusted: false },
    window: {
      async showErrorMessage(message) {
        errors.push(message);
      },
    },
  };

  const result = await withSelectedAgent(
    vscode,
    () => {
      clientCalls += 1;
      return { getAgents: async () => [] };
    },
    undefined,
    async () => {
      actionCalls += 1;
    },
  );

  assert.equal(result.status, "error");
  assert.equal(clientCalls, 0);
  assert.equal(actionCalls, 0);
  assert.match(errors[0], /non approuvé/);
});

test("une commande Git transmet directement l'agent fourni dans un workspace approuvé", async () => {
  const agent = { id: 4, name: "Writer" };
  let selected;
  const result = await withSelectedAgent(
    { workspace: { isTrusted: true }, window: {} },
    () => {
      throw new Error("l'API ne doit pas être consultée");
    },
    { kind: "agent", agent },
    async (candidate) => {
      selected = candidate;
      return { status: "done" };
    },
  );

  assert.equal(result.status, "done");
  assert.equal(selected, agent);
});
