import { resolve } from "node:path";
import { describe, expect, it, vi } from "vitest";
import {
  loadConfigFromProcess,
  loadConfigFromEnv,
  parseAllowedUserIds,
  parseMaxFileSize,
  resolveRepoRootFromModule,
} from "../src/config.js";

describe("parseAllowedUserIds", () => {
  it("parses comma-separated Telegram user IDs", () => {
    expect(parseAllowedUserIds("123, 456")).toEqual([123, 456]);
  });

  it("rejects empty allowlists", () => {
    expect(() => parseAllowedUserIds("")).toThrow("TELEGRAM_ALLOWED_USER_IDS");
  });

  it("rejects non-integer IDs", () => {
    expect(() => parseAllowedUserIds("abc")).toThrow("Invalid Telegram user id");
  });

  it("rejects non-decimal IDs", () => {
    expect(() => parseAllowedUserIds("1e3")).toThrow(
      "Invalid Telegram user id",
    );
    expect(() => parseAllowedUserIds("0x10")).toThrow(
      "Invalid Telegram user id",
    );
  });

  it("rejects zero and negative IDs", () => {
    expect(() => parseAllowedUserIds("0")).toThrow("Invalid Telegram user id");
    expect(() => parseAllowedUserIds("-1")).toThrow("Invalid Telegram user id");
  });
});

describe("parseMaxFileSize", () => {
  it("uses the default when unset", () => {
    expect(parseMaxFileSize(undefined)).toBe(20 * 1024 * 1024);
  });

  it("parses positive integer byte sizes", () => {
    expect(parseMaxFileSize("1024")).toBe(1024);
  });

  it("rejects non-decimal byte sizes", () => {
    expect(() => parseMaxFileSize("1e3")).toThrow("MAX_FILE_SIZE");
    expect(() => parseMaxFileSize("0x10")).toThrow("MAX_FILE_SIZE");
    expect(() => parseMaxFileSize("1.5")).toThrow("MAX_FILE_SIZE");
  });

  it("rejects zero and negative byte sizes", () => {
    expect(() => parseMaxFileSize("0")).toThrow("MAX_FILE_SIZE");
    expect(() => parseMaxFileSize("-1")).toThrow("MAX_FILE_SIZE");
  });
});

describe("loadConfigFromEnv", () => {
  it("loads required values and defaults", () => {
    const config = loadConfigFromEnv(
      {
        TELEGRAM_BOT_TOKEN: "token",
        TELEGRAM_ALLOWED_USER_IDS: "123",
      },
      "D:/GitHub/diet-coach",
    );

    expect(config.telegramBotToken).toBe("token");
    expect(config.telegramAllowedUserIdSet.has(123)).toBe(true);
    expect(config.workspace).toBe("D:/GitHub/diet-coach");
    expect(config.maxFileSize).toBe(20 * 1024 * 1024);
    expect(config.codexSandboxMode).toBe("workspace-write");
    expect(config.codexApprovalPolicy).toBe("never");
  });
});

describe("loadConfigFromProcess", () => {
  it("ignores a missing .env file when the environment provides required values", () => {
    const loadEnv = vi.fn(() => {
      const error = new Error("missing .env") as NodeJS.ErrnoException;
      error.code = "ENOENT";
      throw error;
    });
    const config = loadConfigFromProcess(
      {
        TELEGRAM_BOT_TOKEN: "token",
        TELEGRAM_ALLOWED_USER_IDS: "123",
      },
      "D:/GitHub/diet-coach",
      loadEnv,
    );

    expect(loadEnv).toHaveBeenCalledWith(
      resolve("D:/GitHub/diet-coach", ".env"),
    );
    expect(config.telegramBotToken).toBe("token");
    expect(config.telegramAllowedUserIds).toEqual([123]);
  });
});

describe("resolveRepoRootFromModule", () => {
  it("resolves the repo root from a source module URL", () => {
    expect(
      resolveRepoRootFromModule("file:///D:/GitHub/diet-coach/src/config.ts"),
    ).toBe("D:\\GitHub\\diet-coach");
  });

  it("resolves the repo root from a built module URL", () => {
    expect(
      resolveRepoRootFromModule(
        "file:///D:/GitHub/diet-coach/dist/src/config.js",
      ),
    ).toBe("D:\\GitHub\\diet-coach");
  });
});
