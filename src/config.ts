import { basename, dirname, resolve } from "node:path";
import { loadEnvFile } from "node:process";
import { fileURLToPath } from "node:url";
import type { ApprovalMode, SandboxMode } from "@openai/codex-sdk";

const defaultMaxFileSize = 20 * 1024 * 1024;
const sandboxModes = [
  "read-only",
  "workspace-write",
  "danger-full-access",
] as const satisfies readonly SandboxMode[];
const approvalPolicies = [
  "never",
  "on-request",
  "on-failure",
  "untrusted",
] as const satisfies readonly ApprovalMode[];

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

type ConfigEnv = Record<string, string | undefined>;
type LoadEnvFile = (file?: string) => void;

export function loadConfig(): DietCoachConfig {
  const repoRoot = resolveRepoRootFromModule(import.meta.url);
  return loadConfigFromProcess(process.env, repoRoot, loadEnvFile);
}

export function loadConfigFromProcess(
  env: ConfigEnv,
  workspace: string,
  loadEnv: LoadEnvFile,
): DietCoachConfig {
  try {
    loadEnv(resolve(workspace, ".env"));
  } catch (error) {
    if (!isNodeError(error) || error.code !== "ENOENT") {
      throw error;
    }
  }

  return loadConfigFromEnv(env, workspace);
}

export function resolveRepoRootFromModule(moduleUrl: string): string {
  const moduleDir = dirname(fileURLToPath(moduleUrl));
  const parentDir = dirname(moduleDir);

  if (basename(moduleDir) === "src") {
    return basename(parentDir) === "dist" ? dirname(parentDir) : parentDir;
  }

  return parentDir;
}

export function loadConfigFromEnv(
  env: ConfigEnv,
  workspace: string,
): DietCoachConfig {
  const telegramBotToken = parseRequiredString(
    env.TELEGRAM_BOT_TOKEN,
    "TELEGRAM_BOT_TOKEN",
  );
  const telegramAllowedUserIds = parseAllowedUserIds(
    env.TELEGRAM_ALLOWED_USER_IDS,
  );

  return {
    telegramBotToken,
    telegramAllowedUserIds,
    telegramAllowedUserIdSet: new Set(telegramAllowedUserIds),
    workspace,
    maxFileSize: parseMaxFileSize(env.MAX_FILE_SIZE),
    codexApiKey: parseOptionalString(env.CODEX_API_KEY),
    codexModel: parseOptionalString(env.CODEX_MODEL),
    codexSandboxMode: parseEnum(
      env.CODEX_SANDBOX_MODE,
      "CODEX_SANDBOX_MODE",
      sandboxModes,
      "workspace-write",
    ),
    codexApprovalPolicy: parseEnum(
      env.CODEX_APPROVAL_POLICY,
      "CODEX_APPROVAL_POLICY",
      approvalPolicies,
      "never",
    ),
  };
}

export function parseAllowedUserIds(raw: string | undefined): number[] {
  if (!raw?.trim()) {
    throw new Error("TELEGRAM_ALLOWED_USER_IDS must not be empty");
  }

  return raw.split(",").map((part) => {
    const trimmed = part.trim();

    if (!isDecimalIntegerString(trimmed)) {
      throw new Error(`Invalid Telegram user id: ${trimmed}`);
    }

    const value = Number(trimmed);
    if (!Number.isSafeInteger(value) || value <= 0) {
      throw new Error(`Invalid Telegram user id: ${trimmed}`);
    }

    return value;
  });
}

export function parseMaxFileSize(raw: string | undefined): number {
  if (!raw?.trim()) {
    return defaultMaxFileSize;
  }

  const trimmed = raw.trim();
  if (!isDecimalIntegerString(trimmed)) {
    throw new Error("MAX_FILE_SIZE must be a positive decimal integer byte size");
  }

  const value = Number(trimmed);
  if (!Number.isSafeInteger(value) || value <= 0) {
    throw new Error("MAX_FILE_SIZE must be a positive decimal integer byte size");
  }

  return value;
}

function parseRequiredString(raw: string | undefined, name: string): string {
  const value = raw?.trim();
  if (!value) {
    throw new Error(`${name} must not be empty`);
  }

  return value;
}

function parseOptionalString(raw: string | undefined): string | undefined {
  const value = raw?.trim();
  return value || undefined;
}

function parseEnum<T extends string>(
  raw: string | undefined,
  name: string,
  allowedValues: readonly T[],
  defaultValue: T,
): T {
  const value = raw?.trim();
  if (!value) {
    return defaultValue;
  }

  if (allowedValues.includes(value as T)) {
    return value as T;
  }

  throw new Error(`${name} must be one of: ${allowedValues.join(", ")}`);
}

function isDecimalIntegerString(value: string): boolean {
  return /^\d+$/.test(value);
}

function isNodeError(error: unknown): error is NodeJS.ErrnoException {
  return error instanceof Error && "code" in error;
}
