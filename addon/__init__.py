"""Tap to Flip: choose a single key, including a standalone modifier."""

import sys

from aqt import mw
from aqt.qt import (
    QAction, QApplication, QCheckBox, QDialog, QDialogButtonBox, QEvent,
    QHBoxLayout, QKeySequence, QLabel, QObject, QPushButton, Qt, QTimer, QVBoxLayout,
)

MODULE = __name__
COMMAND = int(Qt.Key.Key_Control if sys.platform == "darwin" else Qt.Key.Key_Meta)
MODIFIERS = {
    int(Qt.Key.Key_Control): Qt.KeyboardModifier.ControlModifier,
    int(Qt.Key.Key_Meta): Qt.KeyboardModifier.MetaModifier,
    int(Qt.Key.Key_Alt): Qt.KeyboardModifier.AltModifier,
    int(Qt.Key.Key_Shift): Qt.KeyboardModifier.ShiftModifier,
}


def key_name(key):
    if key == COMMAND:
        return "Command (⌘)" if sys.platform == "darwin" else "Windows / Super"
    if key == int(Qt.Key.Key_Meta) and sys.platform == "darwin":
        return "Control (⌃)"
    if key == int(Qt.Key.Key_Alt):
        return "Option (⌥)" if sys.platform == "darwin" else "Alt"
    if key == int(Qt.Key.Key_Shift):
        return "Shift"
    if key == int(Qt.Key.Key_Control):
        return "Control"
    return QKeySequence(key).toString(QKeySequence.SequenceFormat.NativeText) or "Unknown"


def other_modifiers(event, key):
    flags = event.modifiers()
    return flags & ~MODIFIERS.get(key, Qt.KeyboardModifier.NoModifier)


class FlipController(QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        config = window.addonManager.getConfig(MODULE) or {}
        self.enabled = bool(config.get("enabled", True))
        self.key = config.get("key", COMMAND)
        if not isinstance(self.key, int) or isinstance(self.key, bool):
            self.key = COMMAND
        self.dialog = None
        self.capture = False
        self.capture_key = None
        self.reset()
        QApplication.instance().installEventFilter(self)

    def reset(self):
        self.armed = False
        self.card = None
        self.pending_card = None

    def queue_flip(self, card):
        # Leave native/WebEngine keyboard dispatch before requesting JavaScript.
        self.pending_card = card

        def reveal():
            if self.pending_card is not card:
                return
            self.pending_card = None
            if self.can_flip() and self.window.reviewer.card is card:
                self.window.reviewer.onEnterKey()

        QTimer.singleShot(0, reveal)

    def can_flip(self):
        reviewer = getattr(self.window, "reviewer", None)
        return (
            self.enabled
            and QApplication.activeWindow() is self.window
            and QApplication.activePopupWidget() is None
            and self.window.state == "review"
            and reviewer is not None
            and reviewer.state == "question"
            and reviewer.card is not None
        )

    def eventFilter(self, obj, event):
        kind = event.type()
        if kind in (QEvent.Type.ApplicationDeactivate, QEvent.Type.WindowDeactivate):
            self.reset()
            if self.capture and self.dialog:
                self.dialog.stop_capture()
            return False

        if self.capture and self.dialog:
            if kind == QEvent.Type.ShortcutOverride:
                event.accept()
                return True
            if kind in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
                if event.isAutoRepeat():
                    return True
                key = event.key()
                # Qt WebEngine forwards modifier events again with an empty key.
                if key == 0:
                    return False
                if key == int(Qt.Key.Key_Escape):
                    self.dialog.stop_capture()
                    return True
                if kind == QEvent.Type.KeyPress:
                    if key in (int(Qt.Key.Key_unknown), int(Qt.Key.Key_CapsLock)):
                        self.dialog.hint.setText("Choose a different key. Caps Lock and Fn are unsupported.")
                    elif not other_modifiers(event, key):
                        self.capture_key = key
                    else:
                        self.capture_key = None
                elif key == self.capture_key:
                    self.dialog.selected_key = key
                    self.dialog.stop_capture()
                return True
            return False

        if kind in (
            QEvent.Type.Shortcut, QEvent.Type.MouseButtonPress,
            QEvent.Type.MouseButtonDblClick, QEvent.Type.Wheel,
        ):
            self.reset()
            return False

        if kind not in (
            QEvent.Type.KeyPress, QEvent.Type.KeyRelease, QEvent.Type.ShortcutOverride,
        ):
            return False

        key = event.key()
        # The real modifier arrives at QWindow/QQuickWidget first. WebEngine
        # then forwards an empty ShortcutOverride/KeyPress through its parents.
        # This is the same input, not a second key that should cancel the tap.
        if key == 0:
            return False
        # ShortcutOverride arrives even when Qt consumes a shortcut before KeyPress.
        if key != self.key:
            if kind in (QEvent.Type.KeyPress, QEvent.Type.ShortcutOverride):
                self.reset()
            return False
        if event.isAutoRepeat():
            return self.armed and self.key not in MODIFIERS
        if not self.can_flip():
            self.reset()
            return False
        if other_modifiers(event, key):
            self.reset()
            return False

        if kind == QEvent.Type.ShortcutOverride:
            # Reserve ordinary keys before Anki shortcuts can consume them.
            if self.key not in MODIFIERS:
                event.accept()
                return True
            return False
        if kind == QEvent.Type.KeyPress:
            self.armed = True
            self.card = self.window.reviewer.card
        elif kind == QEvent.Type.KeyRelease:
            # A modifier release is delivered to several objects. Only the
            # first delivery owns the tap; later copies must not cancel it.
            if not self.armed:
                return False
            flip = self.armed and self.card is self.window.reviewer.card
            card = self.card
            self.reset()
            if flip:
                self.queue_flip(card)
        # Modifier events must continue through Qt for normal combinations to work.
        return self.key not in MODIFIERS

    def show_settings(self):
        if self.dialog:
            self.dialog.raise_()
            self.dialog.activateWindow()
            return
        self.reset()
        self.dialog = Settings(self)
        try:
            self.dialog.exec()
        finally:
            self.capture = False
            self.capture_key = None
            self.dialog = None
            self.reset()


class Settings(QDialog):
    def __init__(self, controller):
        super().__init__(controller.window)
        self.controller = controller
        self.selected_key = controller.key
        self.setWindowTitle("Tap to Flip — Settings")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        self.enabled = QCheckBox("Enable custom flip key")
        self.enabled.setChecked(controller.enabled)
        layout.addWidget(self.enabled)
        row = QHBoxLayout()
        self.current = QLabel(key_name(self.selected_key))
        row.addWidget(self.current, 1)
        self.choose = QPushButton("Choose key…")
        self.choose.clicked.connect(self.start_capture)
        row.addWidget(self.choose)
        layout.addLayout(row)
        self.hint = QLabel()
        self.hint.setWordWrap(True)
        layout.addWidget(self.hint)
        description = QLabel(
            "Tap and release your chosen key to reveal the answer.\n"
            "It only works on the question side while the review window is active.\n\n"
            "Command works on its own. Using it with another key, such as ⌘+C, "
            "won’t trigger this add-on. Either Command key works.\n\n"
            "This key only reveals answers; it never selects a rating."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        self.buttons.accepted.connect(self.save)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.stop_capture()

    def start_capture(self):
        self.controller.reset()
        self.controller.capture = True
        self.controller.capture_key = None
        self.choose.setText("Listening…")
        self.hint.setText("Press and release one key, including ⌘. Press Escape to cancel.")
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setEnabled(False)

    def stop_capture(self):
        self.controller.capture = False
        self.controller.capture_key = None
        self.current.setText(key_name(self.selected_key))
        self.choose.setText("Choose key…")
        self.hint.setText("Changes take effect when you click Save.")
        self.buttons.button(QDialogButtonBox.StandardButton.Save).setEnabled(True)

    def save(self):
        config = self.controller.window.addonManager.getConfig(MODULE) or {}
        config.update(enabled=self.enabled.isChecked(), key=self.selected_key)
        self.controller.window.addonManager.writeConfig(MODULE, config)
        self.controller.enabled = config["enabled"]
        self.controller.key = self.selected_key
        self.controller.reset()
        self.accept()


controller = FlipController(mw)
mw.addonManager.setConfigAction(MODULE, controller.show_settings)
settings_action = QAction("Tap to Flip Settings…", mw)
settings_action.triggered.connect(controller.show_settings)
mw.form.menuTools.addAction(settings_action)
