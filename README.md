# Tap to Flip

A small Anki desktop add-on that reveals the answer when you tap and release a chosen key, including Command alone on macOS. Command is selected by default.

## Install

1. Download **Tap to Flip.ankiaddon** from the [latest release](https://github.com/cobeycobb/Tap-to-Flip/releases/latest).
2. Open Anki → Tools → Add-ons → Install from file, select the download, then fully quit and reopen Anki.
3. Open Tools → Add-ons, select **Tap to Flip**, and click **Config**. You can also use Tools → **Tap to Flip Settings…**.
4. Click **Choose key…**, press and release Command or another single key, then click **Save**.
5. Start reviewing. Tap and release your key to reveal the answer.

Changes in settings take effect immediately. The binding works on the question side of the active review window, including typed-answer cards. It never grades a card. The existing Anki shortcuts remain available; on the question side the chosen ordinary key takes priority over its existing action. On the answer side ordinary keys retain Anki's normal behavior.

If **Config** shows a JSON editor instead of the **Choose key…** dialog, the add-on has not loaded. Fully quit Anki with Command+Q and reopen it. Closing the Add-ons window alone does not load newly installed add-ons. After startup, **Tap to Flip Settings…** should appear in the Tools menu.

Command combinations such as Command+C cancel the pending tap. Clicking, changing windows, or changing cards also cancels it. Either Command key can be used; left and right are not separately selectable. Hold only one Command key at a time. Caps Lock and Fn are unsupported. This captures a single key, not combinations.

## Remove

Disable **Enable custom flip key** in settings, or disable/delete **Tap to Flip** from Anki's add-on manager and restart Anki. No card, deck, template, scheduling, or collection changes are made by this add-on.

## Compatibility

Built for Anki 25.09+ with Qt 6 on macOS. Uses Anki's bundled Qt; no dependencies to install. No global keyboard listener or macOS Accessibility permission is needed. Settings are saved through Anki's add-on configuration.

Verified on Anki 25.09.4 with a physical Command tap. Other operating systems have not been verified. Modifier keys reveal only; a chosen ordinary key can retain Anki's existing rating behavior on the answer side.

## Build

Run `python3 build.py`. The installable archive contains only the files in `addon/`.

## Validation

Fifteen isolated Qt checks cover key capture, saved settings, review state, shortcut conflicts, deferred reveals, and the macOS WebEngine modifier event sequence captured during live debugging. With an Anki Python environment that provides `aqt` and PyQt6, run:

```sh
python build.py
QT_QPA_PLATFORM=offscreen python qa/check_qt.py addon/__init__.py
```

Physical Command input was also confirmed in the running Anki reviewer.

## AnkiWeb description

[ANKIWEB.md](ANKIWEB.md) contains the listing text, with an [HTML version](ANKIWEB.html) for pasting into AnkiWeb.

## Feedback

Report problems through [GitHub Issues](https://github.com/cobeycobb/Tap-to-Flip/issues), including your Anki version, macOS version, selected key, and whether the settings dialog appears.
