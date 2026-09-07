// @vitest-environment node
import { afterEach, describe, expect, it, vi } from "vitest";

const apiFetch = vi.fn();
vi.mock("@/lib/api/client", () => ({
  apiFetch: (...a: unknown[]) => apiFetch(...a),
  ApiError: class ApiError extends Error {},
}));

import { loginRequest } from "./auth-api";

describe("auth-api/loginRequest", () => {
  afterEach(() => apiFetch.mockReset());

  it("POSTs {email, password} to /api/v1/auth/login", async () => {
    apiFetch.mockResolvedValueOnce({ access_token: "a", refresh_token: "r" });

    const tokens = await loginRequest("user@example.com", "pw");

    const [path, init] = apiFetch.mock.calls[0];
    expect(path).toBe("/api/v1/auth/login");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body)).toEqual({ email: "user@example.com", password: "pw" });
    expect(tokens).toEqual({ access_token: "a", refresh_token: "r" });
  });

  it("propagates apiFetch errors (e.g. 401)", async () => {
    apiFetch.mockRejectedValueOnce(new Error("Could not validate credentials"));
    await expect(loginRequest("x@y.z", "bad")).rejects.toThrow("Could not validate credentials");
  });
});
