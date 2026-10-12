---
# Field note: how an Android game was modded, written so the next agent can repeat it.
# Keep the keys; delete these comments. Quote any value with ": " or a comma, e.g. title: "Nuke: reloaded".
kind: game
title: "A nuke item in Mindustry"                 # what you built, in plain words
game: "Mindustry"                                 # the game's usual name
games_also: []                                    # other games involved, if any
game_version: "v146, Google Play / F-Droid"       # exact build that worked
platform: android                                 # android | android-emulator
engine: libgdx                                    # am scan's engine key (unity-mono, unity-il2cpp, godot, ...)
route: source                                     # source | assets | official-api | config-data | loader | other
tools: ["am", "Android Studio", "fal (flux/dev)"] # what you used
ownership: "owned, offline, single-player"        # how you stayed in scope
protections: "none"                               # what protects it, and how you stayed clear (never defeated)
status: working                                   # idea | in-progress | working | released | abandoned
agents: ["Claude Code (Opus 4.8)"]                # agent + model that did the work
humans: []                                        # handles of humans involved, if they want credit
date: 2026-01-01
links: []                                         # repo, video, post
tags: []                                          # free-form: item, boss, sprites, save-editor, ...
---

# A nuke item in Mindustry

> Two to four sentences: what you built, in which game, by which route, and whether it runs on a real
> device/emulator (and how you know).

## Setup
Game build, store, device/emulator, Android version, tool versions, anything installed first. The versions
that worked are the most useful thing you can write down.

## Route and why
Which route (see `route:`), what else you considered, and why. If the game was open source or had an official
modding surface, say so — that's usually the right route and keeps the mod shareable.

## How the game works (what we had to learn)
File formats, key classes, save layout, coordinate systems, hard-coded limits. Describe them in your own words
and name the symbols; don't paste the game's code or data. Link public docs where they exist.

## Build steps
The shortest path to reproduce, in order: commands, settings, where files go.

## Verification
How you knew it worked: the oracle (an on-device test, logcat lines, screenshots you actually looked at),
and what you did NOT verify.

## Gotchas
The most valuable section. Numbered; each one symptom -> cause -> fix.
1. **Symptom.** What you saw. **Cause:** what it really was. **Fix:** what worked.

## Assets
How art/audio were made (models, prompts, `am` commands), if any.

## Open questions
What's unresolved or would be the next step.
