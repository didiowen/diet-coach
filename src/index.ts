import { GrammyError, HttpError } from "grammy";
import { createBot } from "./bot.js";
import { loadConfig } from "./config.js";

const config = loadConfig();
const bot = createBot(config);

bot.catch((error) => {
  const updateId = error.ctx.update.update_id;

  if (error.error instanceof GrammyError) {
    console.error("Telegram handler failed", {
      updateId,
      type: "grammy",
      description: error.error.description,
    });
    return;
  }

  if (error.error instanceof HttpError) {
    console.error("Telegram handler failed", {
      updateId,
      type: "http",
      message: error.error.message,
    });
    return;
  }

  console.error("Telegram handler failed", {
    updateId,
    type: "unknown",
    error: error.error,
  });
});

console.log("Starting diet-coach Codex Telegram bot");
console.log(`Workspace: ${config.workspace}`);

let stopping = false;
function stopBot(signal: NodeJS.Signals): void {
  if (stopping) {
    return;
  }

  stopping = true;
  console.log(`Received ${signal}; stopping bot`);
  bot.stop();
}

process.once("SIGINT", () => stopBot("SIGINT"));
process.once("SIGTERM", () => stopBot("SIGTERM"));

await bot.start({
  drop_pending_updates: true,
});
