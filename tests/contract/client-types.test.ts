import type { components, paths } from "../../packages/contracts/generated/api.js";

const request: components["schemas"]["RetrievalRequest"] = {
  query: "What is supported?",
  dataset_version_ids: ["00000000-0000-0000-0000-000000000001"],
};
const health: paths["/health"]["get"]["responses"][200]["content"]["application/json"] = {
  status: "ok",
};

// @ts-expect-error The generated contract requires explicit version scope.
const invalid: components["schemas"]["RetrievalRequest"] = { query: "missing scope" };
void [request, health, invalid];
