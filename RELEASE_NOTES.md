Tap and release Command (⌘) alone to reveal an answer in Anki on macOS, or choose another single key in **Tools → Tap to Flip Settings…**.

This release handles the extra empty modifier events emitted by Qt WebEngine, preserves Command combinations such as ⌘+C, and queues the reveal after keyboard dispatch completes. It only reveals answers and does not assign a rating.

## Install

1. Download **Tap to Flip.ankiaddon** below.
2. In Anki, open **Tools → Add-ons → Install from file…** and choose the download.
3. Fully quit and reopen Anki.
4. Open **Tools → Tap to Flip Settings…**. Command is selected by default.

Built for Anki desktop on macOS with Qt 6. Verified on Anki 25.09.4 with a physical Command tap, plus 15 isolated Qt checks. Other operating systems have not been verified.
