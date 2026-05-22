---
name: new-cog
description: Use when asked to create a new Discord Cog (.py file in cogs/). Covers file structure, hybrid commands, listeners, project import conventions, and the required setup() function.
---

# new-cog: Building Discord Cogs

Use this skill whenever the user asks you to create a new Cog file for their Discord bot. Follow the conventions below strictly.

## File location

- File goes in `cogs/<CogName>.py`
- File name is **PascalCase** matching the class name (e.g. class `FooBarBot` → `cogs/FooBarBot.py`)

## Mandatory structure

Every cog must have this skeleton — nothing more unless the user explicitly requests additional features:

```python
import discord

from discord.ext import commands
from typing import Any, List, Optional, Dict


class SomeNameBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # --- commands & listeners go here, only if the user asked for them ---

async def setup(bot):
    await bot.add_cog(SomeNameBot(bot))
```

### Rules

1. **`__init__` always takes `bot`** — no extra init params unless user specifies them.
2. **`async def setup(bot)`** — module-level function at the **bottom** of the file. This is what `startBot.py` calls when loading the cog dynamically.
3. **Typing imports** — always include `from typing import Any, List, Optional, Dict` at the top.
4. **`discord` import** — always import `discord` at the top. No other imports unless needed.

## Imports (add only when needed)

When the user's request involves specific functionality, add the corresponding import. Do **not** add them preemptively:

| If they ask about… | Import |
|---|---|
| AI / Gemini | `import gemini_ai_text_prompt` + `import str_formatter` |
| YouTube / audio / voice | `from yt_dl_helper import fetchYoutubeInfo` — `import media.MediaControlsContainer` — `import media.TrackedDurationFFmpegPCMAudio` — `import utils.MediaUtil` — `import time` |
| Voice join detect / DM nudges | `import asyncio` — reference `self.bot.discordUserHelper` |
| Steam API | `from repositories.SteamRepository import SteamRepository` — `from repositories.steam_models import (...)` |
| Message splitting | `import str_formatter` (has `split_message(text, limit=1900)`) |
| Text sanitization | `import str_formatter` (has `sanitize_text(text)`) |
| Guild members / guild data | `from guild_data_helper import getGuildMembers, getGuild, resolve_member_for_id, printMembers, as_int_guild_id` |

## Commands (only if the user asked for a command)

Only add hybrid commands when the user explicitly asks for a command. Do **not** include them by default.

- Use **`@commands.hybrid_command`** (not `@bot.command` or `@app_commands.command`).
- Always provide `name`, `description`, and `brief`.
- Use `await ctx.defer()` before any async work (avoids interaction timeout).
- Reply with `await ctx.reply(...)`. Use `ephemeral=True` for user-only responses.
- Reply in chunks (≤1900 chars) via `str_formatter.split_message()` for long text.

## Listeners

- Use `@commands.Cog.listener()` on async methods inside the class.
- Common events: `on_message`, `on_voice_state_update`, `on_ready`.
- Always guard `on_message` with `if message.author == self.bot.user: return`.

## Bot properties (only if explicitly asked)

The bot exposes these properties on `self.bot`:

- `self.bot.connectedGuilds` — dict of `{guild_id: guild}` set in `on_ready`
- `self.bot.discordUserHelper` — `DiscordUserHelper` instance with `dm_user(user_id, message)` method

**Do not access these unless the user specifically says they need guild data or DM functionality.**

## UI components (only if explicitly asked)

discord.py 2.7.1 supports rich UI via `discord.ui`:

- `discord.ui.LayoutView` — base for views with layout
- `discord.ui.Container` — groups sections/rows
- `discord.ui.Section` — content section with optional accessory (e.g. `Thumbnail`)
- `discord.ui.ActionRow` — row of buttons
- `discord.ui.TextDisplay` — display text
- `discord.ui.Separator` — visual separator
- `discord.ui.Thumbnail` — image thumbnail
- `discord.ui.Button` — clickable button (use `@discord.ui.button(...)` decorator on methods in an `ActionRow` subclass)

**Do not add any UI components unless the user explicitly asks for interactive controls.**

## Repositories (only if explicitly asked)

API repositories live in `repositories/` and follow an async pattern:

- `SteamRepository(api_key: str | None = None, ...)` — has typed methods like `get_player_summaries`, `get_owned_games`, etc.
- Returns typed dataclass models from `repositories.steam_models`

Declare repo instances in `__init__` when needed:
```python
self.steam = SteamRepository()
```

## Template (minimal — default)

Use this when the user says "create a cog for X" without specifying details:

```python
import discord

from discord.ext import commands
from typing import Any, List, Optional, Dict


class MyNewBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(MyNewBot(bot))
```

## What NOT to include

- ❌ Bot properties (`connectedGuilds`, `discordUserHelper`) unless asked
- ❌ UI components (`LayoutView`, containers, buttons) unless asked
- ❌ Repository classes unless asked
- ❌ Media / audio imports unless the cog is about audio
- ❌ Hybrid commands (`@commands.hybrid_command`) unless the user asked for a command
- ❌ Listeners (`@commands.Cog.listener()`) unless the user asked for event handling
- ❌ Any commented-out code in the generated file
