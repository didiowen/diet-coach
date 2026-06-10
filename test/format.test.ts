import { describe, expect, it } from "vitest";
import {
  TELEGRAM_MESSAGE_LIMIT,
  escapeHtml,
  splitTelegramText,
} from "../src/format.js";

describe("escapeHtml", () => {
  it("escapes Telegram HTML special characters", () => {
    expect(escapeHtml("A & B < C > D")).toBe("A &amp; B &lt; C &gt; D");
  });
});

describe("splitTelegramText", () => {
  it("preserves short text as a single message", () => {
    expect(splitTelegramText("short message")).toEqual(["short message"]);
  });

  it("splits long text at a nearby newline when possible", () => {
    const text = `first line\n${"x".repeat(12)}`;

    expect(splitTelegramText(text, 11)).toEqual(["first line\n", "xxxxxxxxxxx", "x"]);
  });

  it("splits long text at a nearby space when possible", () => {
    expect(splitTelegramText("alpha beta gamma", 10)).toEqual([
      "alpha ",
      "beta gamma",
    ]);
  });

  it("hard-splits text when no whitespace is available", () => {
    expect(splitTelegramText("abcdefghij", 4)).toEqual(["abcd", "efgh", "ij"]);
  });

  it("uses the Telegram message limit by default", () => {
    const chunks = splitTelegramText("x".repeat(TELEGRAM_MESSAGE_LIMIT + 1));

    expect(chunks).toHaveLength(2);
    expect(chunks[0]).toHaveLength(TELEGRAM_MESSAGE_LIMIT);
    expect(chunks[1]).toBe("x");
  });
});
