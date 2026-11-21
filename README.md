```
   ██╗  ██╗███████╗██████╗ ██████╗ ██████╗
   ██║  ██║██╔════╝██╔══██╗██╔══██╗██╔══██╗
   ███████║█████╗  ██████╔╝██║  ██║██████╔╝
   ██╔══██║██╔══╝  ██╔══██╗██║  ██║██╔══██╗
   ██║  ██║███████╗██║  ██║██████╔╝██║  ██║
   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝
                                  c o n f i g
        _____
     __/     \__        ┌──────────┬──────────┐
    /  o   o    \~~     │ agent 1  │ agent 2  │
   |     ▼       |      │  ◐ busy  │  ● idle  │
    \   \_/     /       ├──────────┴──────────┤
     \_________/        │ agent 3   ◌ waiting │
      ||     ||         └─────────────────────┘
      ^^     ^^           keep the herd in line.
```

My personal [herdr](https://github.com/herdrdev/herdr) setup — the terminal
multiplexer for wrangling a herd of coding agents.

## ✦ What's inside

| Setting            | Value                                          |
| ------------------ | ---------------------------------------------- |
| 🎨 Theme           | neon green + cyan (custom colors on `gruvbox`)  |
| ⌨️  Prefix          | `ctrl+b` — `prefix + b` toggles sidebar, `prefix + a` / `prefix + A` cycles agents, `prefix + shift + 1..9` focuses agent 1–9, `prefix + =` equalizes pane widths |
| 📑 Tab bar         | bottom, numbered tabs (`1:dev`, `2:git`), zoom · hostname · `HH:MM` · status |
| 🏷️  Pane borders    | show agent labels                              |
| 🔔 Notifications   | toasts off, sounds on                          |
| 🚦 Status          | symbol indicators                              |

## ✦ Install

```sh
# back up anything already there
[ -d ~/.config/herdr ] && mv ~/.config/herdr ~/.config/herdr.bak

git clone https://github.com/AnnupKapur/herdr-config.git ~/.config/herdr

# link the tab-numbers plugin (prefixes tabs with 1:, 2:, 3: ...)
herdr plugin link ~/.config/herdr/plugins/tab-numbers
```

Restart herdr and you're done.

## ✦ Layout

```
~/.config/herdr
├── config.toml        ← the good stuff
├── equalize-panes.py  ← equalizes pane widths (`prefix + =`)
├── plugins/
│   └── tab-numbers/   ← prefixes tab bar labels with 1-based position (`1:dev`, `2:git`)
├── README.md          ← you are here
└── .gitignore         ← keeps the noise out
```

Not tracked (machine-local / runtime): `*.sock`, `*.log`, `session.json`,
`release-notes.json`, `plugins.json`, `.plugins.lock`.

## ✦ Status script

The tab bar calls `~/.config/herdr/status.sh` every 5s (2s timeout).
Drop an executable script there and whatever it prints shows up on the right
side of the tab bar.

```
  ───────────────────────────────────────────────
     🐑 🐑 🐑   herd responsibly   🐑 🐑 🐑
  ───────────────────────────────────────────────
```
