import { request } from "./apiClient";

export function createApproval(payload) {
  return request({
    url: "/approvals",
    method: "POST",
    data: payload,
  });
}
