import { mkdtemp, readFile, stat } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import type { Api } from "grammy";
import { afterEach, describe, expect, it, vi } from "vitest";
import {
  buildPhotoPath,
  cleanupStagedPhotoTurn,
  downloadTelegramFile,
  sanitizeFilename,
  stagePhotoBuffer,
} from "../src/telegram-files.js";

describe("sanitizeFilename", () => {
  it("keeps safe filename characters", () => {
    expect(sanitizeFilename("meal-photo_01.jpg")).toBe("meal-photo_01.jpg");
  });

  it("removes path traversal and replaces unsafe characters", () => {
    expect(sanitizeFilename("../../bad:name?.jpg")).toBe("bad_name_.jpg");
    expect(sanitizeFilename("..\\..\\secret.png")).toBe("secret.png");
  });

  it("falls back when the name has no safe filename content", () => {
    expect(sanitizeFilename("../..")).toBe("photo");
  });

  it("prefixes Windows reserved device basenames", () => {
    expect(sanitizeFilename("CON")).toBe("_CON");
    expect(sanitizeFilename("nul.JPG")).toBe("_nul.JPG");
    expect(sanitizeFilename("COM1.photo.jpg")).toBe("_COM1.photo.jpg");
    expect(sanitizeFilename("lpt9.png")).toBe("_lpt9.png");
  });
});

describe("buildPhotoPath", () => {
  it("builds paths under the workspace inbox turn directory", () => {
    const workspace = path.join(tmpdir(), "diet-coach-test");
    const localPath = buildPhotoPath(workspace, "turn-1", "../meal.jpg");
    const expectedDirectory = path.join(
      workspace,
      ".diet-coach",
      "inbox",
      "turn-1",
    );

    expect(localPath).toBe(path.join(expectedDirectory, "meal.jpg"));
    expect(path.relative(expectedDirectory, localPath)).toBe("meal.jpg");
  });

  it("rejects turn IDs that would escape the inbox", () => {
    expect(() =>
      buildPhotoPath(path.join(tmpdir(), "diet-coach-test"), "../evil", "x.jpg"),
    ).toThrow("turnId");
  });
});

describe("stagePhotoBuffer", () => {
  it("rejects files larger than the configured limit", async () => {
    await expect(
      stagePhotoBuffer(Buffer.from("too large"), tmpdir(), "turn-1", "x.jpg", 3),
    ).rejects.toThrow("maximum");
  });

  it("writes the staged photo under the turn inbox directory", async () => {
    const workspace = await mkdtemp(path.join(tmpdir(), "diet-coach-"));
    const staged = await stagePhotoBuffer(
      Buffer.from("image bytes"),
      workspace,
      "turn-1",
      "../meal.jpg",
      20,
    );

    expect(staged.safeName).toBe("meal.jpg");
    expect(await readFile(staged.localPath, "utf8")).toBe("image bytes");
    expect(
      path.relative(
        path.join(workspace, ".diet-coach", "inbox", "turn-1"),
        staged.localPath,
      ),
    ).toBe("meal.jpg");
  });

  it("uses a collision-resistant filename without overwriting existing staged photos", async () => {
    const workspace = await mkdtemp(path.join(tmpdir(), "diet-coach-"));
    const first = await stagePhotoBuffer(
      Buffer.from("first"),
      workspace,
      "turn-1",
      "meal.jpg",
      20,
    );
    const second = await stagePhotoBuffer(
      Buffer.from("second"),
      workspace,
      "turn-1",
      "meal.jpg",
      20,
    );

    expect(first.safeName).toBe("meal.jpg");
    expect(second.safeName).toBe("meal-1.jpg");
    expect(await readFile(first.localPath, "utf8")).toBe("first");
    expect(await readFile(second.localPath, "utf8")).toBe("second");
    expect(
      path.relative(
        path.join(workspace, ".diet-coach", "inbox", "turn-1"),
        second.localPath,
      ),
    ).toBe("meal-1.jpg");
  });
});

describe("cleanupStagedPhotoTurn", () => {
  it("removes only the requested staged photo turn directory", async () => {
    const workspace = await mkdtemp(path.join(tmpdir(), "diet-coach-"));
    await stagePhotoBuffer(
      Buffer.from("delete me"),
      workspace,
      "turn-delete",
      "meal.jpg",
      20,
    );
    const kept = await stagePhotoBuffer(
      Buffer.from("keep me"),
      workspace,
      "turn-keep",
      "meal.jpg",
      20,
    );

    await cleanupStagedPhotoTurn(workspace, "turn-delete");

    await expect(
      stat(path.join(workspace, ".diet-coach", "inbox", "turn-delete")),
    ).rejects.toMatchObject({ code: "ENOENT" });
    expect(await readFile(kept.localPath, "utf8")).toBe("keep me");
  });
});

describe("downloadTelegramFile", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("downloads a Telegram file returned by the Bot API", async () => {
    const api = {
      getFile: vi.fn().mockResolvedValue({ file_path: "photos/file.jpg" }),
    } as unknown as Api;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        arrayBuffer: vi
          .fn()
          .mockResolvedValue(new Uint8Array([1, 2, 3]).buffer),
      }),
    );

    const buffer = await downloadTelegramFile(api, "token", "file-id");

    expect(api.getFile).toHaveBeenCalledWith("file-id");
    expect(fetch).toHaveBeenCalledWith(
      "https://api.telegram.org/file/bottoken/photos/file.jpg",
    );
    expect(buffer).toEqual(Buffer.from([1, 2, 3]));
  });

  it("rejects Telegram files without a file path", async () => {
    const api = {
      getFile: vi.fn().mockResolvedValue({}),
    } as unknown as Api;

    await expect(downloadTelegramFile(api, "token", "file-id")).rejects.toThrow(
      "file_path",
    );
  });
});
