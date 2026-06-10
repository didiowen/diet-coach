export const TELEGRAM_MESSAGE_LIMIT = 4000;

export function escapeHtml(text: string): string {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

export function splitTelegramText(
  text: string,
  limit = TELEGRAM_MESSAGE_LIMIT,
): string[] {
  if (limit <= 0) {
    throw new RangeError("limit must be greater than zero");
  }

  if (text.length <= limit) {
    return [text];
  }

  const chunks: string[] = [];
  let remaining = text;

  while (remaining.length > limit) {
    const splitAt = findSplitIndex(remaining, limit);
    chunks.push(remaining.slice(0, splitAt));
    remaining = remaining.slice(splitAt);
  }

  if (remaining.length > 0) {
    chunks.push(remaining);
  }

  return chunks;
}

function findSplitIndex(text: string, limit: number): number {
  const window = text.slice(0, limit);
  const newlineIndex = window.lastIndexOf("\n");
  if (newlineIndex > 0) {
    return newlineIndex + 1;
  }

  const spaceIndex = window.lastIndexOf(" ");
  if (spaceIndex > 0) {
    return spaceIndex + 1;
  }

  return limit;
}
