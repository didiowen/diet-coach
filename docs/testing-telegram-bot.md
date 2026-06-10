# Testing The Telegram Bot

This guide checks whether the Codex-backed Telegram bot works end to end.

Do not commit `.env`. This repository ignores `.env*` and keeps only `.env.example`.

## 1. Prerequisites

- Node.js 22 or newer.
- A Telegram bot token from `@BotFather`.
- Your numeric Telegram user ID.
- Codex CLI authenticated on this machine, or `CODEX_API_KEY` in `.env`.
- Network access to `https://api.telegram.org`.

## 2. Configure `.env`

Create `D:\GitHub\diet-coach\.env` from `.env.example`.

Required:

```dotenv
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_USER_IDS=
```

Optional:

```dotenv
CODEX_API_KEY=
CODEX_MODEL=
CODEX_SANDBOX_MODE=workspace-write
CODEX_APPROVAL_POLICY=never
MAX_FILE_SIZE=20971520
```

`TELEGRAM_ALLOWED_USER_IDS` must be your numeric Telegram user ID. Multiple IDs can be comma-separated.

## 3. Check Telegram API Access

Run these commands before starting the bot:

```powershell
Test-NetConnection api.telegram.org -Port 443
curl.exe -I https://api.telegram.org
node -e "fetch('https://api.telegram.org').then(r=>console.log(r.status)).catch(e=>console.error(e.name, e.message))"
```

Expected:

- `TcpTestSucceeded: True`
- `curl.exe` reaches Telegram and returns an HTTP response.
- Node prints an HTTP status, commonly `404`.

If these fail, the bot cannot receive Telegram updates from this network. Try a home network, phone hotspot, VPN, or an allowed proxy.

## 4. Start The Bot

```powershell
cd D:\GitHub\diet-coach
npm install
npm run dev
```

Expected terminal output:

```text
Starting diet-coach Codex Telegram bot
Workspace: D:\GitHub\diet-coach
Starting Telegram polling
Telegram bot: @your_bot_username (123456789)
```

If `Telegram bot: ...` does not appear and you see `Telegram getMe failed`, the bot still cannot reach Telegram Bot API.

## 5. Smoke Tests In Telegram

Send `/start` in a private chat with the bot.

Expected terminal log:

```text
Telegram update received {
  updateId: ...,
  fromId: ...,
  chatId: ...,
  chatType: 'private',
  messageKind: 'command'
}
```

Expected Telegram reply:

```text
diet-coach Codex bot 已就緒。請傳送餐點文字或食物照片。
```

Send `/help`.

Expected: a short usage message for meal text and food photos.

Send a text meal:

```text
早餐：飯糰一顆、無糖豆漿一瓶
```

Expected:

- Telegram first shows `處理中...`.
- The message is edited to the Codex diet-coach response.
- If `SKILL.md` rules require a CSV update, local CSV files are updated.

Send a food photo with a caption:

```text
晚餐，雞腿便當
```

Expected:

- Terminal log says `messageKind: 'photo'`.
- The bot replies after Codex processes the local image.
- Temporary photo files under `.diet-coach/inbox/<turn-id>/` are cleaned after the turn.

## 6. Access-Control Tests

Send a message from a Telegram account not listed in `TELEGRAM_ALLOWED_USER_IDS`.

Expected:

```text
Unauthorized
```

Terminal log should include:

```text
Telegram update rejected by allowlist
```

Add the bot to a group and send a message.

Expected:

```text
此 bot 僅支援私人聊天，請私訊使用。
```

Terminal log should include:

```text
Telegram update rejected outside private chat
```

## 7. Concurrency Test

Send two normal meal messages quickly.

Expected:

- The first message is processed.
- The second receives:

```text
上一則訊息仍在處理中，請稍候。
```

## 8. Log Interpretation

`Telegram bot: @...` does not match the bot you are messaging:

- The token in `.env` belongs to a different bot.

No `Telegram update received` after messaging the bot:

- The process is not receiving updates.
- Common causes: blocked `api.telegram.org`, wrong bot, another process polling the same token, or stale webhook/polling state.

`Telegram update rejected by allowlist`:

- Put the logged `fromId` into `TELEGRAM_ALLOWED_USER_IDS`.

`Telegram update rejected outside private chat`:

- Test in a private chat with the bot.

`Telegram getMe failed`:

- The bot cannot reach Telegram Bot API.
- Re-run the API access checks in section 3.

`Codex` authentication errors:

- Run `codex login` on this machine, or set `CODEX_API_KEY` in `.env`.

## 9. Before Committing Anything

Check that `.env` is ignored:

```powershell
git status --short
git check-ignore .env
```

Expected:

- `.env` is not shown by `git status`.
- `git check-ignore .env` prints `.env`.
