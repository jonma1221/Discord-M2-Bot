# Discord M2 Bot

## Entrypoints

- **`python startBot.py`** — production entrypoint (cog-based). Loads cogs from `cogs/` dynamically.
- **`python example_bot.py`** — older monolithic version (on_message handler for AI + nudge). Not loaded by startBot.
- **`python fetch_guild_details.py [guild_id]`** — standalone diagnostic script. Requires `DISCORD_TOKEN` env var.

## Env

- `.env` is loaded by both entrypoints via `python-dotenv`. Required: `DISCORD_TOKEN`, `DISCORD_GUILD_ID`.
- `.env` is **not** in `.gitignore` — do not commit it. Add `.env` to `.gitignore` before any commit.
- Guild ID in `.env` may have inline comments after `#` — `as_int_guild_id()` strips whitespace but does not strip comments, so keep the comment on a separate var or handle it.

## Architecture

- **discord.py 2.7.1** — hybrid commands (`@commands.hybrid_command`), new `LayoutView`/`Container`/`Section`/`ActionRow` UI components.
- Cogs (`cogs/`): `GeminiAIBot` (AI chat), `NotifyBot` (voice join → DM nudge), `PlayAudioBot` (youtube playback with media controls).
- `utils/`: `DiscordUserHelper` (DM abstraction), `MediaUtil` (time formatting).
- `media/`: `TrackedDurationFFmpegPCMAudio` (PCMVolumeTransformer subclass tracking playback position), `MediaControlsContainer` (rich UI with play/pause/stop/volume), `MediaControls` (older simpler UI).
- `repositories/`: `SteamRepositoryInterface` (ABC interface), `SteamRepository` (Steam Web API), `steam_models` (dataclass response models).
- `bot.connectedGuilds` is set in `on_ready` and read by `NotifyBot`.
- `bot.discordUserHelper` is set in `startBot.py` (not in `example_bot.py` — it uses a module-level var instead).

## Intents Required (Discord Developer Portal)

- `message_content` — for AI bot reading messages
- `voice_states` — for voice join detection and nudge
- `members` (Server Members Intent) — for `guild.fetch_members()`

## Missing Dependencies

`requirements.txt` is stale — it lacks `google-genai` and `yt-dlp`. Both are installed in the venv but not tracked. Add them if regenerating.

## API Keys

- `gemini_ai_text_prompt.py` has a hardcoded API key — should be moved to `.env` or a secrets manager.
- OpenAI key is not in `.env` — `open_ai_text_prompt.py` uses `OpenAI()` which reads `OPENAI_API_KEY` env var.
- `STEAM_API_KEY` goes in `.env` — read by `SteamRepository` via `os.getenv`.

## Commands

- `$send_ai_prompt <prompt>` (hybrid) — ask Gemini AI, replies in chunks (≤1900 chars, split on newlines).
- `$play <youtube_url>` (hybrid) — joins user's voice channel, streams audio via yt-dlp + FFmpeg, shows rich media controls.
- `$volume <0-100>` (hybrid) — adjust playback volume (float conversion, no range clamping).
- `$skip <seconds>` (hybrid) — seek forward by re-creating FFmpeg source with `-ss`.

## Media Playback Notes

- `TrackedDurationFFmpegPCMAudio.read()` increments `currentTime` by 20ms per call (assumes 20ms FFmpeg frames). Use `checkTimestampInSec()` for position.
- `$skip` re-creates the audio source entirely (stop + new FFmpegPCMAudio) — loses track of cumulative seek time.
- Default volume is 0.1 (10%). Volume changes assume `source` is a `PCMVolumeTransformer`.

## Nudge Logic (`NotifyBot`)

When a non-bot member joins a voice channel: scans all guild members, DMs any non-bot member not currently in a voice channel with "Hop on, it's time to start!". Runs as `asyncio.create_task`.

## Scaffolding New Cogs

Use the `new-cog` subagent (`new-cog`) or the `new-cog` skill to scaffold new Cogs. The skill provides conventions and a minimal template. Run it by describing what you want — e.g. "Create a cog that posts Steam deals every hour." Only includes what you ask for (no bot properties, UI components, or repos unless specified).
