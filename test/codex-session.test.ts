import { describe, expect, it } from "vitest";
import {
  buildCodexEnv,
  buildCodexInput,
  buildDietCoachPrompt,
} from "../src/codex-session.js";

describe("buildDietCoachPrompt", () => {
  it("wraps Telegram text with diet-coach context", () => {
    const prompt = buildDietCoachPrompt({ text: "早餐：飯糰和豆漿" });

    expect(prompt.text).toContain("Use SKILL.md in this repository");
    expect(prompt.text).toContain("早餐：飯糰和豆漿");
    expect(prompt.text).toContain("Traditional Chinese");
  });

  it("includes local image paths as Codex image inputs", () => {
    const prompt = buildDietCoachPrompt({
      text: "午餐",
      imagePaths: ["D:/GitHub/diet-coach/.diet-coach/inbox/turn/photo.jpg"],
    });

    expect(prompt.imagePaths).toEqual([
      "D:/GitHub/diet-coach/.diet-coach/inbox/turn/photo.jpg",
    ]);
  });
});

describe("buildCodexEnv", () => {
  it("excludes Telegram secrets from the Codex subprocess environment", () => {
    const env = buildCodexEnv({
      PATH: "C:/Windows/System32",
      CODEX_HOME: "D:/CodexProfile",
      APPDATA: "C:/Users/test/AppData/Roaming",
      LOCALAPPDATA: "C:/Users/test/AppData/Local",
      TELEGRAM_BOT_TOKEN: "telegram-token",
      TELEGRAM_ALLOWED_USER_IDS: "123",
    });

    expect(env).toEqual({
      PATH: "C:/Windows/System32",
      CODEX_HOME: "D:/CodexProfile",
      APPDATA: "C:/Users/test/AppData/Roaming",
      LOCALAPPDATA: "C:/Users/test/AppData/Local",
    });
  });

  it("includes CODEX_API_KEY only when explicitly configured", () => {
    expect(buildCodexEnv({}, undefined)).not.toHaveProperty("CODEX_API_KEY");

    expect(buildCodexEnv({}, "codex-key")).toEqual({
      CODEX_API_KEY: "codex-key",
    });
  });
});

describe("buildCodexInput", () => {
  it("converts prompt image paths to Codex local_image inputs", () => {
    const prompt = buildDietCoachPrompt({
      text: "午餐",
      imagePaths: [
        "D:/GitHub/diet-coach/.diet-coach/inbox/turn/photo.jpg",
      ],
    });

    expect(buildCodexInput(prompt)).toEqual([
      { type: "text", text: prompt.text },
      {
        type: "local_image",
        path: "D:/GitHub/diet-coach/.diet-coach/inbox/turn/photo.jpg",
      },
    ]);
  });
});
