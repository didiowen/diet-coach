import type { Bot, Context, RawApi } from "grammy";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createBot } from "../src/bot.js";
import type { DietCoachConfig } from "../src/config.js";
import type { CodexCallbacks, DietCoachPrompt } from "../src/codex-session.js";

interface ApiCall {
  method: keyof RawApi;
  payload: Record<string, unknown>;
}

class FakeSession {
  readonly prompt = vi.fn(
    async (_input: DietCoachPrompt, callbacks: CodexCallbacks) => {
      callbacks.onTextDelta("完成");
      callbacks.onDone();
    },
  );
}

const mocks = vi.hoisted(() => ({
  session: undefined as FakeSession | undefined,
  codexConstructor: vi.fn(),
  downloadTelegramFile: vi.fn(),
  stagePhotoBuffer: vi.fn(),
  cleanupStagedPhotoTurn: vi.fn(),
}));

vi.mock("../src/codex-session.js", () => ({
  CodexSessionService: mocks.codexConstructor,
}));

vi.mock("../src/telegram-files.js", () => ({
  downloadTelegramFile: mocks.downloadTelegramFile,
  stagePhotoBuffer: mocks.stagePhotoBuffer,
  cleanupStagedPhotoTurn: mocks.cleanupStagedPhotoTurn,
}));

describe("createBot", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.session = new FakeSession();
    mocks.codexConstructor.mockImplementation(() => mocks.session);
    mocks.downloadTelegramFile.mockResolvedValue(Buffer.from("photo"));
    mocks.stagePhotoBuffer.mockImplementation(
      async (
        _buffer: Buffer,
        workspace: string,
        turnId: string,
        originalName: string,
      ) => ({
        localPath: `${workspace}/.diet-coach/inbox/${turnId}/${originalName}`,
        safeName: originalName,
      }),
    );
    mocks.cleanupStagedPhotoTurn.mockResolvedValue(undefined);
  });

  it("tells allowed group users to use private chat without creating a Codex session", async () => {
    const bot = createTestBot();
    const calls = captureApiCalls(bot);

    await bot.handleUpdate(textUpdate({ chatType: "supergroup" }) as never);

    expect(mocks.codexConstructor).not.toHaveBeenCalled();
    expect(mocks.session?.prompt).not.toHaveBeenCalled();
    expect(calls).toContainEqual(
      expect.objectContaining({
        method: "sendMessage",
        payload: expect.objectContaining({
          text: expect.stringContaining("私人"),
        }),
      }),
    );
  });

  it("releases the busy state when the initial status reply fails", async () => {
    const bot = createTestBot();
    const calls = captureApiCalls(bot, {
      failFirstStatusReply: true,
    });

    await expect(
      bot.handleUpdate(textUpdate({ text: "早餐" }) as never),
    ).rejects.toThrow("status send failed");
    await bot.handleUpdate(textUpdate({ text: "午餐" }) as never);

    expect(mocks.session?.prompt).toHaveBeenCalledTimes(1);
    expect(
      calls.filter(
        (call) =>
          call.method === "sendMessage" && call.payload.text === "處理中...",
      ),
    ).toHaveLength(2);
  });

  it("cleans staged photo temp paths after prompt handling", async () => {
    const bot = createTestBot();
    captureApiCalls(bot);

    await bot.handleUpdate(photoUpdate() as never);

    const stagedPath = mocks.stagePhotoBuffer.mock.results[0]?.value;
    await expect(stagedPath).resolves.toMatchObject({
      localPath: expect.stringContaining("/.diet-coach/inbox/"),
    });
    expect(mocks.session?.prompt).toHaveBeenCalledWith(
      expect.objectContaining({
        text: "晚餐",
        imagePaths: [expect.stringContaining("/.diet-coach/inbox/")],
      }),
      expect.any(Object),
    );
    expect(mocks.cleanupStagedPhotoTurn).toHaveBeenCalledWith(
      "D:/GitHub/diet-coach",
      expect.any(String),
    );
  });

  it("cleans staged photo temp paths when prompt handling fails", async () => {
    mocks.session?.prompt.mockRejectedValueOnce(new Error("Codex failed"));
    const bot = createTestBot();
    captureApiCalls(bot);

    await bot.handleUpdate(photoUpdate() as never);

    expect(mocks.cleanupStagedPhotoTurn).toHaveBeenCalledWith(
      "D:/GitHub/diet-coach",
      expect.any(String),
    );
  });

  it("releases the busy state when photo cleanup fails", async () => {
    mocks.cleanupStagedPhotoTurn.mockRejectedValueOnce(new Error("cleanup failed"));
    const bot = createTestBot();
    const calls = captureApiCalls(bot);

    await expect(bot.handleUpdate(photoUpdate() as never)).rejects.toThrow(
      "cleanup failed",
    );
    await bot.handleUpdate(textUpdate({ text: "下一餐" }) as never);

    expect(mocks.session?.prompt).toHaveBeenCalledTimes(2);
    expect(
      calls.filter(
        (call) =>
          call.method === "sendMessage" && call.payload.text === "處理中...",
      ),
    ).toHaveLength(2);
  });
});

function createTestBot(): Bot<Context> {
  const bot = createBot(testConfig());
  bot.botInfo = {
    id: 999,
    is_bot: true,
    first_name: "Diet Coach",
    username: "diet_coach_bot",
    can_join_groups: true,
    can_read_all_group_messages: false,
    supports_inline_queries: false,
    can_connect_to_business: false,
    has_main_web_app: false,
  } as never;

  return bot;
}

function captureApiCalls(
  bot: Bot<Context>,
  options: { failFirstStatusReply?: boolean } = {},
): ApiCall[] {
  const calls: ApiCall[] = [];
  let nextMessageId = 100;
  let statusFailuresRemaining = options.failFirstStatusReply ? 1 : 0;

  bot.api.config.use((async (
    _prev: unknown,
    method: keyof RawApi,
    payload: unknown,
  ) => {
    calls.push({ method, payload: payload as Record<string, unknown> });

    if (
      method === "sendMessage" &&
      (payload as { text?: string }).text === "處理中..." &&
      statusFailuresRemaining > 0
    ) {
      statusFailuresRemaining -= 1;
      throw new Error("status send failed");
    }

    if (method === "sendMessage") {
      return {
        ok: true,
        result: {
          message_id: nextMessageId++,
          date: 0,
          chat: {
            id: (payload as { chat_id: number }).chat_id,
            type: "private",
          },
          text: (payload as { text: string }).text,
        },
      };
    }

    if (method === "editMessageText") {
      return { ok: true, result: true };
    }

    throw new Error(`Unexpected Telegram API method: ${String(method)}`);
  }) as never);

  return calls;
}

function testConfig(): DietCoachConfig {
  return {
    telegramBotToken: "token",
    telegramAllowedUserIds: [123],
    telegramAllowedUserIdSet: new Set([123]),
    workspace: "D:/GitHub/diet-coach",
    maxFileSize: 20,
    codexSandboxMode: "workspace-write",
    codexApprovalPolicy: "never",
  };
}

function textUpdate({
  text = "早餐",
  chatType = "private",
}: {
  text?: string;
  chatType?: "private" | "group" | "supergroup";
} = {}) {
  return {
    update_id: 1,
    message: {
      message_id: 1,
      date: 0,
      chat: { id: 456, type: chatType },
      from: { id: 123, is_bot: false, first_name: "User" },
      text,
    },
  };
}

function photoUpdate() {
  return {
    update_id: 2,
    message: {
      message_id: 2,
      date: 0,
      chat: { id: 456, type: "private" },
      from: { id: 123, is_bot: false, first_name: "User" },
      caption: "晚餐",
      photo: [
        {
          file_id: "small-photo",
          file_unique_id: "small",
          width: 320,
          height: 240,
          file_size: 100,
        },
        {
          file_id: "large-photo",
          file_unique_id: "large",
          width: 1280,
          height: 960,
          file_size: 1000,
        },
      ],
    },
  };
}
