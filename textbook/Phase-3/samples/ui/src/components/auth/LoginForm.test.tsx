import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { TamaguiProvider } from "tamagui";
import tamaguiConfig from "../../../tamagui.config";

const loginRequest = vi.fn();
vi.mock("./auth-api", () => ({ loginRequest: (...a: unknown[]) => loginRequest(...a) }));

const replace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace, push: vi.fn(), prefetch: vi.fn() }),
  useSearchParams: () => new URLSearchParams("redirect=/optimization/benchmark"),
}));

// ApiError の実体は client.ts。ここではメッセージ判定のためだけに使う
import { ApiError } from "@/lib/api/client";
import { useAuthStore } from "./auth-store";
import { LoginForm } from "./LoginForm";

function renderForm() {
  return render(
    <TamaguiProvider config={tamaguiConfig} defaultTheme="light">
      <LoginForm />
    </TamaguiProvider>,
  );
}

describe("LoginForm", () => {
  beforeEach(() => {
    loginRequest.mockReset();
    replace.mockReset();
    localStorage.clear();
    useAuthStore.setState({ accessToken: null, refreshToken: null, status: "idle", error: null });
  });
  afterEach(() => vi.restoreAllMocks());

  it("logs in and redirects on success", async () => {
    loginRequest.mockResolvedValueOnce({ access_token: "acc", refresh_token: "ref" });
    const user = userEvent.setup();
    renderForm();

    await user.type(screen.getByLabelText("メールアドレス"), "user@example.com");
    await user.type(screen.getByLabelText("パスワード"), "pw");
    await user.click(screen.getByRole("button", { name: "ログイン" }));

    expect(loginRequest).toHaveBeenCalledWith("user@example.com", "pw");
    expect(useAuthStore.getState().accessToken).toBe("acc");
    expect(useAuthStore.getState().refreshToken).toBe("ref");
    expect(replace).toHaveBeenCalledWith("/optimization/benchmark");
  });

  it("shows the ApiError message on failure and does not redirect", async () => {
    loginRequest.mockRejectedValueOnce(new ApiError(401, "Could not validate credentials"));
    const user = userEvent.setup();
    renderForm();

    await user.type(screen.getByLabelText("メールアドレス"), "x@y.z");
    await user.type(screen.getByLabelText("パスワード"), "bad");
    await user.click(screen.getByRole("button", { name: "ログイン" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Could not validate credentials");
    expect(replace).not.toHaveBeenCalled();
    expect(useAuthStore.getState().accessToken).toBeNull();
  });

  it("shows a logout affordance when already authenticated", () => {
    useAuthStore.setState({ accessToken: "already" });
    renderForm();

    expect(screen.getByText("ログイン中です")).toBeInTheDocument();
    expect(screen.queryByLabelText("メールアドレス")).not.toBeInTheDocument();
  });
});
