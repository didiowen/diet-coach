import { Codex, type Input, type Thread } from "@openai/codex-sdk";
import type { DietCoachConfig } from "./config.js";

export interface DietCoachPrompt {
  text?: string;
  imagePaths?: string[];
}

export interface CodexCallbacks {
  onTextDelta(delta: string): void;
  onDone(): void;
}

export class CodexSessionService {
  private readonly codex: Codex;
  private thread?: Thread;
  private activeTurn?: AbortController;

  constructor(private readonly config: DietCoachConfig) {
    this.codex = new Codex(buildCodexOptions(config));
  }

  async prompt(
    input: DietCoachPrompt,
    callbacks: CodexCallbacks,
  ): Promise<void> {
    if (this.activeTurn) {
      throw new Error("Codex turn already in progress");
    }

    const abortController = new AbortController();
    this.activeTurn = abortController;

    try {
      const prompt = buildDietCoachPrompt(input);
      const streamedTurn = await this.getThread().runStreamed(
        buildCodexInput(prompt),
        { signal: abortController.signal },
      );
      const agentMessageTextById = new Map<string, string>();

      for await (const event of streamedTurn.events) {
        if (
          event.type === "item.started" ||
          event.type === "item.updated" ||
          event.type === "item.completed"
        ) {
          const item = event.item;
          if (item.type === "agent_message") {
            const previousText = agentMessageTextById.get(item.id) ?? "";
            const delta = item.text.slice(previousText.length);
            agentMessageTextById.set(item.id, item.text);

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
      if (this.activeTurn === abortController) {
        this.activeTurn = undefined;
      }
    }
  }

  private getThread(): Thread {
    this.thread ??= this.codex.startThread({
      model: this.config.codexModel,
      workingDirectory: this.config.workspace,
      sandboxMode: this.config.codexSandboxMode,
      approvalPolicy: this.config.codexApprovalPolicy,
      skipGitRepoCheck: true,
    });

    return this.thread;
  }
}

export function buildDietCoachPrompt(
  input: DietCoachPrompt,
): Required<DietCoachPrompt> {
  const userText = input.text?.trim() ?? "";
  const imagePaths = input.imagePaths ?? [];

  return {
    text: [
      "Use SKILL.md in this repository as the diet-coach instruction source.",
      "Treat this as a diet-coach request, not general coding.",
      "Use Traditional Chinese (zh-TW) and Taiwanese terminology.",
      "Update only relevant local CSV files if SKILL.md requires it.",
      "Do not ask user for API keys, tokens, or credentials.",
      "",
      "Telegram user request:",
      userText,
    ].join("\n"),
    imagePaths,
  };
}

export function buildCodexInput(prompt: Required<DietCoachPrompt>): Input {
  return [
    { type: "text", text: prompt.text },
    ...prompt.imagePaths.map((path) => ({ type: "local_image" as const, path })),
  ];
}

function buildCodexOptions(config: DietCoachConfig): ConstructorParameters<
  typeof Codex
>[0] {
  const env = buildCodexEnv(process.env, config.codexApiKey);

  if (!config.codexApiKey) {
    return { env };
  }

  return {
    apiKey: config.codexApiKey,
    env,
  };
}

export function buildCodexEnv(
  sourceEnv: NodeJS.ProcessEnv,
  codexApiKey?: string,
): Record<string, string> {
  const env: Record<string, string> = {};

  for (const key of [
    "PATH",
    "Path",
    "CODEX_HOME",
    "SystemRoot",
    "WINDIR",
    "TEMP",
    "TMP",
    "HOME",
    "USERPROFILE",
    "APPDATA",
    "LOCALAPPDATA",
  ]) {
    const value = sourceEnv[key];
    if (value) {
      env[key] = value;
    }
  }

  if (codexApiKey) {
    env.CODEX_API_KEY = codexApiKey;
  }

  return env;
}
