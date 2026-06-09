# Codex Telegram Bot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Node 22 TypeScript Telegram bot inside `diet-coach` that forwards allowlisted text and food photos to Codex CLI with this repo's diet-coach context.

**Architecture:** Add a small TeleCodex-inspired adapter instead of vendoring the full upstream project. Telegram handlers live in `src/bot.ts`, Codex SDK integration in `src/codex-session.ts`, config validation in `src/config.ts`, and photo staging in `src/telegram-files.ts`.

**Tech Stack:** Node.js 22, TypeScript, `grammy`, `@grammyjs/auto-retry`, `@openai/codex-sdk`, Vitest.

---

## File Structure

- Create `package.json`: npm scripts and dependencies.
- Create `tsconfig.json`: strict TypeScript settings for ESM output.
- Create `vitest.config.ts`: Vitest config.
- Create `.env.example`: documented variables only, no secrets.
- Modify `.gitignore`: ignore `.env`, `.diet-coach/`, `node_modules/`, `dist/`, `coverage/`.
- Create `src/config.ts`: load `.env`, parse allowlist, max file size, Codex settings.
- Create `src/format.ts`: Telegram-safe escaping and message splitting.
- Create `src/telegram-files.ts`: safe file path creation and Telegram download helper.
- Create `src/codex-session.ts`: Codex thread lifecycle and diet-coach prompt builder.
- Create `src/bot.ts`: Telegram commands and message handlers.
- Create `src/index.ts`: startup and polling loop.
- Create `test/config.test.ts`: config parsing tests.
- Create `test/format.test.ts`: message escaping and splitting tests.
- Create `test/telegram-files.test.ts`: staging path safety tests.
- Create `test/codex-session.test.ts`: diet prompt construction tests.
- Modify `README.md`: replace Claude Code plugin-only setup with Codex Telegram bot setup while preserving project explanation.

## Task 1: Project Scaffolding

**Files:**
- Create: `package.json`
- Create: `tsconfig.json`
- Create: `vitest.config.ts`
- Create: `.env.example`
- Modify: `.gitignore`

- [ ] **Step 1: Create Node project files**

Add `package.json`:

```json
{
  "name": "diet-coach",
  "version": "0.4.0",
  "description": "Codex CLI powered Telegram diet coach",
  "license": "MIT",
  "type": "module",
  "scripts": {
    "dev": "tsx src/index.ts",
    "build": "tsc",
    "start": "node dist/index.js",
    "test": "vitest run"
  },
  "dependencies": {
    "@grammyjs/auto-retry": "^2.0.2",
    "@openai/codex-sdk": "^0.116.0",
    "grammy": "^1.41.1"
  },
  "devDependencies": {
    "@types/node": "^25.5.0",
    "tsx": "^4.21.0",
    "typescript": "^5.9.3",
    "vitest": "^3.2.4"
  }
}
```

Add `tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "esModuleInterop": true,
    "forceConsistentCasingInFileNames": true,
    "skipLibCheck": true,
    "outDir": "dist",
    "rootDir": ".",
    "types": ["node"]
  },
  "include": ["src/**/*.ts", "test/**/*.ts", "vitest.config.ts"]
}
```

Add `vitest.config.ts`:

```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
  },
});
```

Add `.env.example`:

```dotenv
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_USER_IDS=
CODEX_API_KEY=
CODEX_MODEL=
CODEX_SANDBOX_MODE=workspace-write
CODEX_APPROVAL_POLICY=never
MAX_FILE_SIZE=20971520
```

- [ ] **Step 2: Add ignore rules**

If `.gitignore` does not exist, create it. Ensure it contains:

```gitignore
.env
.diet-coach/
node_modules/
dist/
coverage/
```

- [ ] **Step 3: Install dependencies**

Run:

```powershell
npm install
```

Expected: `package-lock.json` is created and npm exits 0.

- [ ] **Step 4: Verify baseline test command**

Run:

```powershell
npm test
```

Expected: Vitest reports no test files yet or exits successfully after tests are added in later tasks. If Vitest exits non-zero only because no tests exist, proceed to Task 2 and use later test runs as verification.

- [ ] **Step 5: Commit scaffold only after explicit user approval**

Do not commit automatically. If the user explicitly approves, run:

```powershell
git -c safe.directory=D:/GitHub/diet-coach -C D:\GitHub\diet-coach add -- package.json package-lock.json tsconfig.json vitest.config.ts .env.example .gitignore
git -c safe.directory=D:/GitHub/diet-coach -C D:\GitHub\diet-coach commit -m "Add Codex Telegram bot scaffold"
```

## Task 2: Config Parsing

**Files:**
- Create: `src/config.ts`
- Create: `test/config.test.ts`

- [ ] **Step 1: Write failing config tests**

Add `test/config.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import {
  loadConfigFromEnv,
  parseAllowedUserIds,
  parseMaxFileSize,
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
});

describe("parseMaxFileSize", () => {
  it("uses the default when unset", () => {
    expect(parseMaxFileSize(undefined)).toBe(20 * 1024 * 1024);
  });

  it("parses positive integer byte sizes", () => {
    expect(parseMaxFileSize("1024")).toBe(1024);
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
    expect(config.codexSandboxMode).toBe("workspace-write");
    expect(config.codexApprovalPolicy).toBe("never");
  });
});
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
npm test -- test/config.test.ts
```

Expected: FAIL because `src/config.ts` does not exist.

- [ ] **Step 3: Implement config module**

Add `src/config.ts`:

```ts
import { existsSync, readFileSync } from "node:fs";
import path from "node:path";

import type { ApprovalMode, SandboxMode } from "@openai/codex-sdk";

export interface DietCoachConfig {
  telegramBotToken: string;
  telegramAllowedUserIds: number[];
  telegramAllowedUserIdSet: Set<number>;
  workspace: string;
  maxFileSize: number;
  codexApiKey?: string;
  codexModel?: string;
  codexSandboxMode: SandboxMode;
  codexApprovalPolicy: ApprovalMode;
}

type EnvMap = Record<string, string | undefined>;

export function loadConfig(): DietCoachConfig {
  loadEnvFile(path.resolve(process.cwd(), ".env"));
  return loadConfigFromEnv(process.env, process.cwd());
}

export function loadConfigFromEnv(env: EnvMap, workspace: string): DietCoachConfig {
  const telegramBotToken = requireEnv(env, "TELEGRAM_BOT_TOKEN");
  const telegramAllowedUserIds = parseAllowedUserIds(requireEnv(env, "TELEGRAM_ALLOWED_USER_IDS"));
  const codexSandboxMode = parseSandboxMode(optionalString(env.CODEX_SANDBOX_MODE));
  const codexApprovalPolicy = parseApprovalPolicy(optionalString(env.CODEX_APPROVAL_POLICY));

  return {
    telegramBotToken,
    telegramAllowedUserIds,
    telegramAllowedUserIdSet: new Set(telegramAllowedUserIds),
    workspace,
    maxFileSize: parseMaxFileSize(optionalString(env.MAX_FILE_SIZE)),
    codexApiKey: optionalString(env.CODEX_API_KEY),
    codexModel: optionalString(env.CODEX_MODEL),
    codexSandboxMode,
    codexApprovalPolicy,
  };
}

export function parseAllowedUserIds(raw: string): number[] {
  const ids = raw
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean)
    .map((value) => {
      const parsed = Number(value);
      if (!Number.isInteger(parsed) || parsed <= 0) {
        throw new Error(`Invalid Telegram user id in TELEGRAM_ALLOWED_USER_IDS: ${value}`);
      }
      return parsed;
    });

  if (ids.length === 0) {
    throw new Error("TELEGRAM_ALLOWED_USER_IDS must contain at least one user id");
  }

  return ids;
}

export function parseMaxFileSize(raw: string | undefined): number {
  if (!raw) {
    return 20 * 1024 * 1024;
  }
  const parsed = Number(raw);
  if (!Number.isInteger(parsed) || parsed <= 0) {
    throw new Error(`Invalid MAX_FILE_SIZE: ${raw}`);
  }
  return parsed;
}

function parseSandboxMode(raw: string | undefined): SandboxMode {
  if (!raw) {
    return "workspace-write";
  }
  if (raw === "read-only" || raw === "workspace-write" || raw === "danger-full-access") {
    return raw;
  }
  throw new Error(`Invalid CODEX_SANDBOX_MODE: ${raw}`);
}

function parseApprovalPolicy(raw: string | undefined): ApprovalMode {
  if (!raw) {
    return "never";
  }
  if (raw === "never" || raw === "on-request" || raw === "on-failure" || raw === "untrusted") {
    return raw;
  }
  throw new Error(`Invalid CODEX_APPROVAL_POLICY: ${raw}`);
}

function requireEnv(env: EnvMap, name: string): string {
  const value = optionalString(env[name]);
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function optionalString(value: string | undefined): string | undefined {
  const trimmed = value?.trim();
  return trimmed ? trimmed : undefined;
}

function loadEnvFile(envPath: string): void {
  if (!existsSync(envPath)) {
    return;
  }

  const contents = readFileSync(envPath, "utf8");
  for (const rawLine of contents.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line || line.startsWith("#")) {
      continue;
    }

    const separatorIndex = line.indexOf("=");
    if (separatorIndex === -1) {
      continue;
    }

    const key = line.slice(0, separatorIndex).trim();
    let value = line.slice(separatorIndex + 1).trim();
    if (!key || process.env[key] !== undefined) {
      continue;
    }
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    process.env[key] = value.replace(/\\n/g, "\n");
  }
}
```

- [ ] **Step 4: Run config tests**

Run:

```powershell
npm test -- test/config.test.ts
```

Expected: PASS.

## Task 3: Formatting And Photo Staging Helpers

**Files:**
- Create: `src/format.ts`
- Create: `src/telegram-files.ts`
- Create: `test/format.test.ts`
- Create: `test/telegram-files.test.ts`

- [ ] **Step 1: Write failing format tests**

Add `test/format.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { escapeHtml, splitTelegramText } from "../src/format.js";

describe("escapeHtml", () => {
  it("escapes Telegram HTML-sensitive characters", () => {
    expect(escapeHtml("<b>&x</b>")).toBe("&lt;b&gt;&amp;x&lt;/b&gt;");
  });
});

describe("splitTelegramText", () => {
  it("keeps short text in one chunk", () => {
    expect(splitTelegramText("hello", 10)).toEqual(["hello"]);
  });

  it("splits long text within the limit", () => {
    expect(splitTelegramText("hello world", 6)).toEqual(["hello", "world"]);
  });
});
```

- [ ] **Step 2: Write failing staging tests**

Add `test/telegram-files.test.ts`:

```ts
import path from "node:path";
import { describe, expect, it } from "vitest";
import { buildPhotoPath, sanitizeFilename } from "../src/telegram-files.js";

describe("sanitizeFilename", () => {
  it("removes path traversal and unsafe characters", () => {
    expect(sanitizeFilename("../bad name.jpg")).toBe("bad_name.jpg");
  });
});

describe("buildPhotoPath", () => {
  it("keeps staged photos under the workspace inbox", () => {
    const result = buildPhotoPath("D:/GitHub/diet-coach", "turn-1", "meal photo.jpg");
    expect(result).toBe(path.join("D:/GitHub/diet-coach", ".diet-coach", "inbox", "turn-1", "meal_photo.jpg"));
  });
});
```

- [ ] **Step 3: Run tests to verify failure**

Run:

```powershell
npm test -- test/format.test.ts test/telegram-files.test.ts
```

Expected: FAIL because helper modules do not exist.

- [ ] **Step 4: Implement format helpers**

Add `src/format.ts`:

```ts
export const TELEGRAM_MESSAGE_LIMIT = 4000;

export function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

export function splitTelegramText(text: string, limit = TELEGRAM_MESSAGE_LIMIT): string[] {
  if (text.length <= limit) {
    return [text];
  }

  const chunks: string[] = [];
  let remaining = text.trim();

  while (remaining.length > limit) {
    const splitAt = findSplitIndex(remaining, limit);
    chunks.push(remaining.slice(0, splitAt).trim());
    remaining = remaining.slice(splitAt).trim();
  }

  if (remaining) {
    chunks.push(remaining);
  }

  return chunks;
}

function findSplitIndex(text: string, limit: number): number {
  const newlineIndex = text.lastIndexOf("\n", limit);
  if (newlineIndex > 0) {
    return newlineIndex;
  }
  const spaceIndex = text.lastIndexOf(" ", limit);
  if (spaceIndex > 0) {
    return spaceIndex;
  }
  return limit;
}
```

- [ ] **Step 5: Implement photo staging helpers**

Add `src/telegram-files.ts`:

```ts
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import type { Api } from "grammy";

const UNSAFE_FILENAME_CHARS = /[^a-zA-Z0-9._-]/g;
const PATH_TRAVERSAL = /\.\./g;

export interface StagedPhoto {
  localPath: string;
  safeName: string;
}

export function sanitizeFilename(name: string): string {
  const basename = name.split(/[\\/]/).pop() ?? name;
  const cleaned = basename.replace(PATH_TRAVERSAL, "").replace(UNSAFE_FILENAME_CHARS, "_");
  return cleaned || "photo.jpg";
}

export function buildPhotoPath(workspace: string, turnId: string, originalName: string): string {
  return path.join(workspace, ".diet-coach", "inbox", turnId, sanitizeFilename(originalName));
}

export async function stagePhotoBuffer(
  buffer: Buffer,
  workspace: string,
  turnId: string,
  originalName: string,
  maxFileSize: number,
): Promise<StagedPhoto> {
  if (buffer.byteLength > maxFileSize) {
    throw new Error(`Photo too large (${buffer.byteLength} bytes, max ${maxFileSize})`);
  }

  const localPath = buildPhotoPath(workspace, turnId, originalName);
  await mkdir(path.dirname(localPath), { recursive: true });
  await writeFile(localPath, buffer);
  return { localPath, safeName: path.basename(localPath) };
}

export async function downloadTelegramFile(api: Api, botToken: string, fileId: string): Promise<Buffer> {
  const file = await api.getFile(fileId);
  if (!file.file_path) {
    throw new Error("Telegram did not return a file path");
  }

  const response = await fetch(`https://api.telegram.org/file/bot${botToken}/${file.file_path}`);
  if (!response.ok) {
    throw new Error(`Telegram file download failed: ${response.status}`);
  }

  return Buffer.from(await response.arrayBuffer());
}
```

- [ ] **Step 6: Run helper tests**

Run:

```powershell
npm test -- test/format.test.ts test/telegram-files.test.ts
```

Expected: PASS.

## Task 4: Codex Session Wrapper

**Files:**
- Create: `src/codex-session.ts`
- Create: `test/codex-session.test.ts`

- [ ] **Step 1: Write failing prompt tests**

Add `test/codex-session.test.ts`:

```ts
import { describe, expect, it } from "vitest";
import { buildDietCoachPrompt } from "../src/codex-session.js";

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

    expect(prompt.imagePaths).toEqual(["D:/GitHub/diet-coach/.diet-coach/inbox/turn/photo.jpg"]);
  });
});
```

- [ ] **Step 2: Run tests to verify failure**

Run:

```powershell
npm test -- test/codex-session.test.ts
```

Expected: FAIL because `src/codex-session.ts` does not exist.

- [ ] **Step 3: Implement Codex wrapper**

Add `src/codex-session.ts`:

```ts
import {
  Codex,
  type Input,
  type Thread,
  type UserInput,
} from "@openai/codex-sdk";

import type { DietCoachConfig } from "./config.js";

export interface DietCoachPrompt {
  text?: string;
  imagePaths?: string[];
}

export interface CodexCallbacks {
  onTextDelta: (delta: string) => void;
  onDone: () => void;
}

export class CodexSessionService {
  private readonly codex: Codex;
  private thread: Thread | null = null;
  private abortController: AbortController | null = null;

  constructor(private readonly config: DietCoachConfig) {
    this.codex = new Codex({
      apiKey: config.codexApiKey,
      config: {
        approval_policy: config.codexApprovalPolicy,
      },
      env: buildCodexEnv(config.codexApiKey),
    });
  }

  async prompt(input: DietCoachPrompt, callbacks: CodexCallbacks): Promise<void> {
    if (!this.thread) {
      this.thread = this.codex.startThread({
        model: this.config.codexModel,
        workingDirectory: this.config.workspace,
        sandboxMode: this.config.codexSandboxMode,
        approvalPolicy: this.config.codexApprovalPolicy,
        skipGitRepoCheck: true,
      });
    }

    if (this.abortController) {
      throw new Error("A Codex turn is already in progress");
    }

    const controller = new AbortController();
    this.abortController = controller;
    let lastAgentText = "";

    try {
      const { events } = await this.thread.runStreamed(toCodexInput(buildDietCoachPrompt(input)), {
        signal: controller.signal,
      });

      for await (const event of events) {
        if (event.type === "item.updated" || event.type === "item.completed") {
          const item = event.item;
          if (item.type === "agent_message") {
            const delta = item.text.startsWith(lastAgentText) ? item.text.slice(lastAgentText.length) : item.text;
            lastAgentText = item.text;
            if (delta) {
              callbacks.onTextDelta(delta);
            }
          }
        } else if (event.type === "turn.completed") {
          callbacks.onDone();
        } else if (event.type === "turn.failed") {
          throw new Error(event.error.message);
        } else if (event.type === "error") {
          throw new Error(event.message);
        }
      }
    } finally {
      if (this.abortController === controller) {
        this.abortController = null;
      }
    }
  }
}

export function buildDietCoachPrompt(input: DietCoachPrompt): Required<DietCoachPrompt> {
  const userText = input.text?.trim() || "請根據這張食物照片估算熱量與巨量營養素。";
  const text = [
    "Use SKILL.md in this repository as the diet-coach instruction source.",
    "Treat this as a diet-coach request, not a general coding task.",
    "Use Traditional Chinese (zh-TW) and Taiwanese terminology.",
    "If SKILL.md requires CSV updates, update only the relevant local CSV files in this repository.",
    "Do not ask the user for API keys, tokens, or credentials.",
    "",
    "Telegram user message:",
    userText,
  ].join("\n");

  return {
    text,
    imagePaths: input.imagePaths ?? [],
  };
}

function toCodexInput(input: Required<DietCoachPrompt>): Input {
  const parts: UserInput[] = [{ type: "text", text: input.text }];
  for (const imagePath of input.imagePaths) {
    parts.push({ type: "local_image", path: imagePath });
  }
  return parts.length === 1 ? input.text : parts;
}

function buildCodexEnv(apiKey?: string): Record<string, string> {
  const env: Record<string, string> = {};
  for (const [key, value] of Object.entries(process.env)) {
    if (value !== undefined) {
      env[key] = value;
    }
  }
  if (apiKey) {
    env.CODEX_API_KEY = apiKey;
  }
  return env;
}
```

- [ ] **Step 4: Run Codex prompt tests**

Run:

```powershell
npm test -- test/codex-session.test.ts
```

Expected: PASS.

## Task 5: Telegram Bot And Startup

**Files:**
- Create: `src/bot.ts`
- Create: `src/index.ts`

- [ ] **Step 1: Implement Telegram bot handlers**

Add `src/bot.ts`:

```ts
import { randomUUID } from "node:crypto";
import { autoRetry } from "@grammyjs/auto-retry";
import { Bot, type Context } from "grammy";

import { CodexSessionService, type DietCoachPrompt } from "./codex-session.js";
import type { DietCoachConfig } from "./config.js";
import { escapeHtml, splitTelegramText } from "./format.js";
import { downloadTelegramFile, stagePhotoBuffer } from "./telegram-files.js";

export function createBot(config: DietCoachConfig): Bot<Context> {
  const bot = new Bot<Context>(config.telegramBotToken);
  bot.api.config.use(autoRetry({ maxRetryAttempts: 3, maxDelaySeconds: 10 }));

  const sessions = new Map<number, CodexSessionService>();
  const busyChats = new Set<number>();

  bot.use(async (ctx, next) => {
    const userId = ctx.from?.id;
    if (!userId || !config.telegramAllowedUserIdSet.has(userId)) {
      if (ctx.message) {
        await ctx.reply("Unauthorized");
      }
      return;
    }
    await next();
  });

  bot.command("start", async (ctx) => {
    await ctx.reply("diet-coach Codex bot 已啟動。傳送餐點文字或照片即可估算。");
  });

  bot.command("help", async (ctx) => {
    await ctx.reply([
      "可用方式：",
      "- 傳送餐點文字描述",
      "- 傳送食物照片，可加 caption",
      "",
      "Bot 會把內容交給 Codex，依本 repo 的 SKILL.md 估算並視需要更新 CSV。",
    ].join("\n"));
  });

  bot.on("message:text", async (ctx) => {
    if (ctx.message.text.startsWith("/")) {
      return;
    }
    await handlePrompt(ctx, config, sessions, busyChats, { text: ctx.message.text });
  });

  bot.on("message:photo", async (ctx) => {
    const photos = ctx.message.photo;
    const photo = photos[photos.length - 1];
    if (!photo) {
      await ctx.reply("沒有收到可處理的照片。");
      return;
    }

    const turnId = randomUUID();
    const buffer = await downloadTelegramFile(ctx.api, config.telegramBotToken, photo.file_id);
    const staged = await stagePhotoBuffer(buffer, config.workspace, turnId, "photo.jpg", config.maxFileSize);
    await handlePrompt(ctx, config, sessions, busyChats, {
      text: ctx.message.caption,
      imagePaths: [staged.localPath],
    });
  });

  return bot;
}

async function handlePrompt(
  ctx: Context,
  config: DietCoachConfig,
  sessions: Map<number, CodexSessionService>,
  busyChats: Set<number>,
  input: DietCoachPrompt,
): Promise<void> {
  const chatId = ctx.chat?.id;
  if (!chatId) {
    return;
  }

  if (busyChats.has(chatId)) {
    await ctx.reply("上一則訊息仍在處理中，請稍候。");
    return;
  }

  let session = sessions.get(chatId);
  if (!session) {
    session = new CodexSessionService(config);
    sessions.set(chatId, session);
  }

  busyChats.add(chatId);
  let accumulated = "";
  const statusMessage = await ctx.reply("處理中...");

  try {
    await session.prompt(input, {
      onTextDelta(delta) {
        accumulated += delta;
      },
      onDone() {},
    });

    const finalText = accumulated.trim() || "Codex 沒有回傳內容。";
    const chunks = splitTelegramText(finalText);
    await ctx.api.editMessageText(chatId, statusMessage.message_id, escapeHtml(chunks[0] ?? ""), {
      parse_mode: "HTML",
    });
    for (const chunk of chunks.slice(1)) {
      await ctx.reply(escapeHtml(chunk), { parse_mode: "HTML" });
    }
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    await ctx.api.editMessageText(chatId, statusMessage.message_id, `錯誤：${escapeHtml(message)}`, {
      parse_mode: "HTML",
    });
  } finally {
    busyChats.delete(chatId);
  }
}
```

- [ ] **Step 2: Implement startup file**

Add `src/index.ts`:

```ts
import { createBot } from "./bot.js";
import { loadConfig } from "./config.js";

const config = loadConfig();
const bot = createBot(config);

console.log("diet-coach Codex Telegram bot running");
console.log(`Workspace: ${config.workspace}`);

let shuttingDown = false;
const shutdown = (signal: NodeJS.Signals) => {
  if (shuttingDown) {
    return;
  }
  shuttingDown = true;
  console.log(`Received ${signal}, stopping bot...`);
  bot.stop();
};

process.once("SIGINT", () => shutdown("SIGINT"));
process.once("SIGTERM", () => shutdown("SIGTERM"));

await bot.start({
  drop_pending_updates: true,
});
```

- [ ] **Step 3: Run TypeScript build**

Run:

```powershell
npm run build
```

Expected: PASS. If the Codex SDK type names differ from the plan, inspect installed package types and adjust the wrapper with the smallest compatible change.

## Task 6: README Update And Final Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Update README setup section**

Edit `README.md` to document:

```md
## Codex Telegram Bot

This version can run as an independent Telegram bot backed by Codex CLI.

### Prerequisites

- Node.js 22+
- Codex CLI installed and authenticated on the host, or `CODEX_API_KEY`
- A Telegram bot token from BotFather
- Your numeric Telegram user ID for `TELEGRAM_ALLOWED_USER_IDS`

### Setup

```bash
npm install
cp .env.example .env
npm run dev
```

Required `.env` values:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USER_IDS`

Send a meal description or food photo to the bot. Codex will use `SKILL.md` in this repository and update local CSV files when the skill rules require it.
```

Keep the existing nutrition, CSV, and BMR/TDEE documentation unless it contradicts the Codex bot setup.

- [ ] **Step 2: Run all tests**

Run:

```powershell
npm test
```

Expected: PASS.

- [ ] **Step 3: Run build**

Run:

```powershell
npm run build
```

Expected: PASS.

- [ ] **Step 4: Check Git status and diff**

Run:

```powershell
git -c safe.directory=D:/GitHub/diet-coach -C D:\GitHub\diet-coach status --short
git -c safe.directory=D:/GitHub/diet-coach -C D:\GitHub\diet-coach diff --check
```

Expected: only intended files changed; `diff --check` exits 0.

- [ ] **Step 5: Ask before commit / push / PR / merge**

After verification, ask the user one short question about whether they want to commit, push, open a PR, or merge. Do not run git publishing commands without explicit approval.

## Self-Review

Spec coverage:

- Text input: Task 5 implements `message:text`.
- Photo input: Tasks 3 and 5 implement download and staging.
- Persistent session per chat: Task 5 stores `CodexSessionService` by chat ID.
- Codex diet-coach context: Task 4 builds fixed prompt text referencing `SKILL.md`.
- Environment config: Tasks 1 and 2 implement `.env.example` and config parsing.
- Safety: Tasks 2, 3, and 5 implement allowlist and safe staging under `.diet-coach/`.
- Verification: Tasks 2 through 6 include tests and build commands.

Placeholder scan:

- No planned code step uses unresolved placeholders.
- The plan intentionally defers real credentials to `.env` and never asks the user for secrets.

Type consistency:

- `DietCoachConfig` is created in `src/config.ts` and consumed by `src/bot.ts` and `src/codex-session.ts`.
- `DietCoachPrompt` is created in `src/codex-session.ts` and consumed by `src/bot.ts`.
- `escapeHtml`, `splitTelegramText`, `downloadTelegramFile`, and `stagePhotoBuffer` names are consistent across tests and implementation steps.
