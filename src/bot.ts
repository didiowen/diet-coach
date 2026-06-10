import { randomUUID } from "node:crypto";
import { autoRetry } from "@grammyjs/auto-retry";
import { Bot, type Context } from "grammy";
import {
  CodexSessionService,
  type CodexCallbacks,
  type DietCoachPrompt,
} from "./codex-session.js";
import type { DietCoachConfig } from "./config.js";
import {
  TELEGRAM_MESSAGE_LIMIT,
  escapeHtml,
  splitTelegramText,
} from "./format.js";
import {
  cleanupStagedPhotoTurn,
  downloadTelegramFile,
  stagePhotoBuffer,
} from "./telegram-files.js";

interface CodexSession {
  prompt(input: DietCoachPrompt, callbacks: CodexCallbacks): Promise<void>;
}

interface PromptTurn {
  input: DietCoachPrompt;
  cleanup?(): Promise<void>;
}

type PromptTurnFactory = () => Promise<PromptTurn>;

export function createBot(config: DietCoachConfig): Bot<Context> {
  const bot = new Bot<Context>(config.telegramBotToken);
  bot.api.config.use(autoRetry());

  const sessions = new Map<number, CodexSession>();
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

  bot.use(async (ctx, next) => {
    if (ctx.chat?.type !== "private") {
      if (ctx.message) {
        await ctx.reply("此 bot 僅支援私人聊天，請私訊使用。");
      }
      return;
    }

    await next();
  });

  bot.command("start", async (ctx) => {
    await ctx.reply(
      "diet-coach Codex bot 已就緒。請傳送餐點文字或食物照片。",
    );
  });

  bot.command("help", async (ctx) => {
    await ctx.reply(
      [
        "使用方式：",
        "1. 傳送餐點文字描述。",
        "2. 傳送食物照片，可加上照片說明。",
        "",
        "Codex 會依本 repo 的 SKILL.md 處理，必要時更新 CSV。",
      ].join("\n"),
    );
  });

  bot.on("message:text", async (ctx) => {
    if (ctx.message.text.startsWith("/")) {
      return;
    }

    await handlePrompt(
      ctx,
      config,
      sessions,
      busyChats,
      async () => ({
        input: { text: ctx.message.text },
      }),
    );
  });

  bot.on("message:photo", async (ctx) => {
    await handlePrompt(ctx, config, sessions, busyChats, async () => {
      const photo = ctx.message.photo.at(-1);
      if (!photo) {
        throw new Error("沒有收到可處理的照片。");
      }

      const turnId = randomUUID();
      const buffer = await downloadTelegramFile(
        ctx.api,
        config.telegramBotToken,
        photo.file_id,
      );
      const staged = await stagePhotoBuffer(
        buffer,
        config.workspace,
        turnId,
        "photo.jpg",
        config.maxFileSize,
      );

      return {
        input: {
          text: ctx.message.caption,
          imagePaths: [staged.localPath],
        },
        cleanup: () => cleanupStagedPhotoTurn(config.workspace, turnId),
      };
    });
  });

  return bot;
}

async function handlePrompt(
  ctx: Context,
  config: DietCoachConfig,
  sessions: Map<number, CodexSession>,
  busyChats: Set<number>,
  createPromptTurn: PromptTurnFactory,
): Promise<void> {
  const chatId = ctx.chat?.id;
  if (!chatId) {
    return;
  }

  if (busyChats.has(chatId)) {
    await ctx.reply("上一則訊息仍在處理中，請稍候。");
    return;
  }

  busyChats.add(chatId);
  let statusMessageId: number | undefined;
  let cleanup: (() => Promise<void>) | undefined;
  let accumulatedText = "";

  try {
    const statusMessage = await ctx.reply("處理中...");
    statusMessageId = statusMessage.message_id;

    let session = sessions.get(chatId);
    if (!session) {
      session = new CodexSessionService(config);
      sessions.set(chatId, session);
    }

    const promptTurn = await createPromptTurn();
    cleanup = promptTurn.cleanup;

    await session.prompt(promptTurn.input, {
      onTextDelta(delta) {
        accumulatedText += delta;
      },
      onDone() {},
    });

    await sendFinalResponse(
      ctx,
      chatId,
      statusMessageId,
      accumulatedText,
    );
  } catch (error) {
    if (!statusMessageId) {
      throw error;
    }

    const message = error instanceof Error ? error.message : String(error);
    await editMessageText(
      ctx,
      chatId,
      statusMessageId,
      `錯誤：${message}`,
    );
  } finally {
    try {
      await cleanup?.();
    } finally {
      busyChats.delete(chatId);
    }
  }
}

async function sendFinalResponse(
  ctx: Context,
  chatId: number,
  statusMessageId: number,
  text: string,
): Promise<void> {
  const chunks = buildTelegramHtmlChunks(text.trim() || "Codex 沒有回傳內容。");
  const [firstChunk, ...remainingChunks] = chunks;

  await editMessageHtml(ctx, chatId, statusMessageId, firstChunk ?? "");
  for (const chunk of remainingChunks) {
    await ctx.reply(chunk, { parse_mode: "HTML" });
  }
}

async function editMessageText(
  ctx: Context,
  chatId: number,
  messageId: number,
  text: string,
): Promise<void> {
  await editMessageHtml(ctx, chatId, messageId, escapeHtml(text));
}

async function editMessageHtml(
  ctx: Context,
  chatId: number,
  messageId: number,
  html: string,
): Promise<void> {
  await ctx.api.editMessageText(chatId, messageId, html, {
    parse_mode: "HTML",
  });
}

function buildTelegramHtmlChunks(text: string): string[] {
  return splitTelegramText(text).flatMap((chunk) => {
    const escaped = escapeHtml(chunk);
    if (escaped.length <= TELEGRAM_MESSAGE_LIMIT) {
      return escaped;
    }

    return splitEscapedText(chunk);
  });
}

function splitEscapedText(text: string): string[] {
  const chunks: string[] = [];
  let current = "";

  for (const character of text) {
    const escapedCharacter = escapeHtml(character);
    if (
      current.length > 0 &&
      current.length + escapedCharacter.length > TELEGRAM_MESSAGE_LIMIT
    ) {
      chunks.push(current);
      current = "";
    }

    current += escapedCharacter;
  }

  if (current) {
    chunks.push(current);
  }

  return chunks;
}
