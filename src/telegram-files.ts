import { mkdir, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import type { Api } from "grammy";

const reservedWindowsDeviceBasenames = new Set([
  "CON",
  "PRN",
  "AUX",
  "NUL",
  "COM1",
  "COM2",
  "COM3",
  "COM4",
  "COM5",
  "COM6",
  "COM7",
  "COM8",
  "COM9",
  "LPT1",
  "LPT2",
  "LPT3",
  "LPT4",
  "LPT5",
  "LPT6",
  "LPT7",
  "LPT8",
  "LPT9",
]);

export interface StagedPhoto {
  localPath: string;
  safeName: string;
}

export function sanitizeFilename(name: string): string {
  const basename = name.split(/[\\/]+/).filter(Boolean).at(-1) ?? "";
  const safeName = basename
    .replaceAll(/[^A-Za-z0-9._-]/g, "_")
    .replaceAll(/_+/g, "_")
    .replaceAll(/^[._-]+|[._-]+$/g, "");

  if (!safeName) {
    return "photo";
  }

  return isReservedWindowsDeviceBasename(safeName) ? `_${safeName}` : safeName;
}

export function buildPhotoPath(
  workspace: string,
  turnId: string,
  originalName: string,
): string {
  if (!isSafePathSegment(turnId)) {
    throw new Error("turnId must be a safe path segment");
  }

  const turnDirectory = path.resolve(
    workspace,
    ".diet-coach",
    "inbox",
    turnId,
  );
  const localPath = path.resolve(turnDirectory, sanitizeFilename(originalName));
  const relativePath = path.relative(turnDirectory, localPath);

  if (relativePath.startsWith("..") || path.isAbsolute(relativePath)) {
    throw new Error("staged photo path escapes the turn inbox directory");
  }

  return localPath;
}

export async function stagePhotoBuffer(
  buffer: Buffer,
  workspace: string,
  turnId: string,
  originalName: string,
  maxFileSize: number,
): Promise<StagedPhoto> {
  if (buffer.length > maxFileSize) {
    throw new Error("Photo exceeds maximum file size");
  }

  const initialSafeName = sanitizeFilename(originalName);
  let safeName = initialSafeName;
  let localPath = buildPhotoPath(workspace, turnId, safeName);

  await mkdir(path.dirname(localPath), { recursive: true });
  for (let index = 0; ; index += 1) {
    if (index > 0) {
      safeName = appendFilenameSuffix(initialSafeName, index);
      localPath = buildPhotoPath(workspace, turnId, safeName);
    }

    try {
      await writeFile(localPath, buffer, { flag: "wx" });
      return { localPath, safeName };
    } catch (error) {
      if (!isNodeError(error) || error.code !== "EEXIST") {
        throw error;
      }
    }
  }
}

export async function downloadTelegramFile(
  api: Api,
  botToken: string,
  fileId: string,
): Promise<Buffer> {
  const file = await api.getFile(fileId);
  if (!file.file_path) {
    throw new Error("Telegram file response did not include file_path");
  }

  const response = await fetch(
    `https://api.telegram.org/file/bot${botToken}/${file.file_path}`,
  );
  if (!response.ok) {
    throw new Error(`Telegram file download failed: ${response.status}`);
  }

  return Buffer.from(await response.arrayBuffer());
}

export async function cleanupStagedPhotoTurn(
  workspace: string,
  turnId: string,
): Promise<void> {
  if (!isSafePathSegment(turnId)) {
    throw new Error("turnId must be a safe path segment");
  }

  const inboxDirectory = path.resolve(workspace, ".diet-coach", "inbox");
  const turnDirectory = path.resolve(inboxDirectory, turnId);
  const relativePath = path.relative(inboxDirectory, turnDirectory);

  if (
    relativePath === "" ||
    relativePath.startsWith("..") ||
    path.isAbsolute(relativePath)
  ) {
    throw new Error("cleanup path escapes the staged photo inbox");
  }

  await rm(turnDirectory, { recursive: true, force: true });
}

function isSafePathSegment(value: string): boolean {
  return /^[A-Za-z0-9._-]+$/.test(value) && value !== "." && value !== "..";
}

function isReservedWindowsDeviceBasename(name: string): boolean {
  const stem = name.split(".", 1)[0] ?? name;

  return reservedWindowsDeviceBasenames.has(stem.toUpperCase());
}

function appendFilenameSuffix(name: string, suffix: number): string {
  const extension = path.extname(name);
  const stem = extension ? name.slice(0, -extension.length) : name;

  return `${stem}-${suffix}${extension}`;
}

function isNodeError(error: unknown): error is NodeJS.ErrnoException {
  return error instanceof Error && "code" in error;
}
