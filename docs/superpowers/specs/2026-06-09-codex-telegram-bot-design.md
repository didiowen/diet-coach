# Codex Telegram Bot Design

Date: 2026-06-09
Branch: codex-telegram-bot

## Goal

Add a Codex CLI powered Telegram bot inside this repository so `diet-coach` can run as an independent Telegram service. The bot receives food descriptions or photos, forwards them to a Codex thread, and lets Codex use this repository's `SKILL.md` plus local CSV files to estimate nutrition and record results.

## Scope

Initial scope:

- Text messages from allowlisted Telegram users.
- Food photos with optional captions.
- A persistent Codex session per Telegram chat.
- Streaming or near-streaming replies back to Telegram.
- Local staging of uploaded photos under `.diet-coach/inbox/`.
- Configuration through environment variables and `.env.example`.
- TypeScript build verification.

Out of scope for the first version:

- Voice transcription.
- Telegram document ingestion.
- Session browser, model picker, launch profile UI, or CLI handback.
- Web app UI.
- Changing `SKILL.md` nutrition rules beyond adding bot-specific setup notes if needed.

## Architecture

The implementation will be a small TypeScript Node 22 project inspired by TeleCodex, not a full copy of TeleCodex.

Main components:

- `src/index.ts`: start-up, config loading, bot polling, shutdown handling.
- `src/config.ts`: reads environment variables, validates Telegram token and allowlist, sets Codex options.
- `src/bot.ts`: Telegram handlers for `/start`, `/help`, text, and photo messages.
- `src/codex-session.ts`: thin wrapper around `@openai/codex-sdk`, fixed to this repository workspace.
- `src/telegram-files.ts`: downloads and stages Telegram photos safely.
- `src/format.ts`: trims and escapes bot replies for Telegram limits.

The Codex working directory will be the repository root. The prompt sent to Codex will explicitly say:

- Use `SKILL.md` in this repo as the diet-coach instruction source.
- Treat the Telegram message as a diet-coach request, not a general coding task.
- Update `diet_log.csv`, `food_reference.csv`, or `weight_log.csv` only when the skill rules require it.
- Keep replies in Traditional Chinese using Taiwanese terminology.

## Data Flow

Text message:

1. Telegram receives text from an allowlisted user.
2. Bot maps the chat to a `CodexSessionService`.
3. Bot sends a diet-coach prompt to Codex.
4. Codex reads local files and performs permitted CSV updates.
5. Bot streams or sends the final response to Telegram.

Photo message:

1. Bot downloads the largest Telegram photo.
2. Bot saves it to `.diet-coach/inbox/<turn-id>/photo.jpg`.
3. Bot sends the local image path plus caption to Codex.
4. Codex estimates the meal or extracts nutrition labels, following `SKILL.md`.
5. Bot replies and removes only temporary staged files created for that turn.

## Configuration

Required:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USER_IDS`

Optional:

- `CODEX_API_KEY`
- `CODEX_MODEL`
- `CODEX_SANDBOX_MODE` default `workspace-write`
- `CODEX_APPROVAL_POLICY` default `never`
- `MAX_FILE_SIZE` default 20 MB

The repo will include `.env.example` only. The implementation will not request tokens interactively and will not inspect a real `.env`.

## Safety

- Only allowlisted Telegram user IDs can interact with the bot.
- Uploaded photo filenames are generated or sanitised before writing.
- Temporary files stay under `.diet-coach/`, which will be gitignored.
- Default Codex sandbox is `workspace-write`, so diet CSV files can be updated while avoiding unrestricted host access.
- The first version will not expose `danger-full-access` controls through Telegram.

## Testing And Verification

Verification for the first implementation:

- `npm install`
- `npm run build`
- Unit tests for config parsing, allowlist checks, and filename/path staging helpers where practical.
- Manual smoke test instructions in README for running `npm run dev` after the user supplies Telegram credentials.

## Acceptance Criteria

- A fresh clone can install dependencies and compile the bot.
- `README.md` documents Codex Telegram setup without relying on Claude Code Telegram plugins.
- `.env.example` documents required and optional variables without containing secrets.
- The bot rejects non-allowlisted users.
- Text and photo messages are forwarded to Codex with diet-coach context.
- Codex runs in the repository workspace and can update the CSV templates according to `SKILL.md`.
