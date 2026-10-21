import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import aqt
from aqt.qt import (QApplication, QMainWindow, QWidget, Qt, QEvent, QKeyEvent,
                    QKeySequence, QShortcut, QDialogButtonBox)
from PyQt6.QtTest import QTest

app = QApplication([])
class Manager:
    config = {"enabled": True, "key": int(Qt.Key.Key_Control)}
    def getConfig(self, module): return self.config.copy()
    def writeConfig(self, module, config): self.config = config.copy()
    def setConfigAction(self, module, callback): self.callback = callback

window = QMainWindow()
window.setWindowTitle('Tap to Flip isolated Qt checks')
window.setCentralWidget(QWidget())
window.addonManager = Manager()
window.form = SimpleNamespace(menuTools=window.menuBar().addMenu('Tools'))
window.state = 'review'
count = [0]
def show_answer():
    count[0] += 1
    window.reviewer.state = 'answer'
window.reviewer = SimpleNamespace(state='question', card=object(), onEnterKey=show_answer)
aqt.mw = window
source = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location('tap_to_flip', source)
addon = importlib.util.module_from_spec(spec)
spec.loader.exec_module(addon)
c = addon.controller
window.show()
window.activateWindow()
window.raise_()
QTest.qWait(200)
assert QApplication.activeWindow() is window
checks = []

def front():
    window.reviewer.state = 'question'
    window.reviewer.card = object()
    c.reset()

def send(kind, key, mods=Qt.KeyboardModifier.NoModifier):
    QApplication.sendEvent(window.centralWidget(), QKeyEvent(kind, key, mods))

press, release = QEvent.Type.KeyPress, QEvent.Type.KeyRelease
cmd, letter = Qt.Key.Key_Control, Qt.Key.Key_C

def tap():
    send(press, cmd)
    send(release, cmd)
    QApplication.processEvents()

front()
send(press, cmd)
assert count[0] == 0
send(release, cmd)
QApplication.processEvents()
assert count[0] == 1
checks.append('Command reveals on release, once')
tap()
assert count[0] == 1
checks.append('Command does not grade the answer')
front()
send(press, cmd)
send(QEvent.Type.ShortcutOverride, letter, Qt.KeyboardModifier.ControlModifier)
send(release, cmd)
assert count[0] == 1
checks.append('Command+C cancels flip even if Qt consumes shortcut')
front()
send(press, cmd)
QApplication.sendEvent(window, QEvent(QEvent.Type.ApplicationDeactivate))
send(release, cmd)
assert count[0] == 1
checks.append('App deactivation cancels pending flip')
front()
send(press, cmd)
window.reviewer.card = object()
send(release, cmd)
assert count[0] == 1
checks.append('Card replacement cancels pending flip')
front()
c.enabled = False
tap()
assert count[0] == 1
c.enabled = True
checks.append('Disabled binding does nothing')
front()
send(press, cmd, Qt.KeyboardModifier.ShiftModifier)
send(release, cmd)
assert count[0] == 1
checks.append('Additional modifiers prevent flip')
front()
window.state = 'deckBrowser'
tap()
assert count[0] == 1
window.state = 'review'
checks.append('Outside review does nothing')

front()
c.key = int(Qt.Key.Key_F)
shortcut_calls = []
shortcut = QShortcut(QKeySequence('F'), window)
shortcut.activated.connect(lambda: shortcut_calls.append(1))
QTest.keyClick(window.centralWidget(), Qt.Key.Key_F)
QApplication.processEvents()
assert count[0] == 2 and not shortcut_calls
checks.append('Ordinary key overrides an existing Qt shortcut on the question side')

# Capture through actual event filter, then save and reload config.
dialog = addon.Settings(c)
c.dialog = dialog
dialog.show()
dialog.activateWindow()
QTest.qWait(100)
dialog.start_capture()
QTest.keyClick(dialog, cmd)
assert dialog.selected_key == int(cmd)
assert not c.capture
assert dialog.current.text() == 'Command (⌘)'
assert dialog.buttons.button(QDialogButtonBox.StandardButton.Save).isEnabled()
dialog.save()
assert window.addonManager.config['key'] == int(cmd)
assert window.addonManager.config['enabled'] is True
c.dialog = None
checks.append('Choose key captures Command alone and Save persists it')

window.activateWindow()
QTest.qWait(100)
front()
tap()
assert count[0] == 3
checks.append('Saved binding applies immediately')

# Replay the real macOS/WebEngine event sequence that broke version 1.0.0.
front()
before = count[0]
sequence = json.loads((source.parent.parent / 'qa' / 'webengine-command-sequence.json').read_text())
for row in sequence:
    send(getattr(QEvent.Type, row['kind']), row['key'], Qt.KeyboardModifier(row['mods']))
assert count[0] == before  # Reveal is deferred until keyboard dispatch ends.
QApplication.processEvents()
assert count[0] == before + 1
checks.append('Real macOS WebEngine empty events and duplicate releases reveal once')

front()
before = count[0]
send(press, cmd)
send(QEvent.Type.ShortcutOverride, 0, Qt.KeyboardModifier.ControlModifier)
send(press, 0, Qt.KeyboardModifier.ControlModifier)
send(QEvent.Type.ShortcutOverride, letter, Qt.KeyboardModifier.ControlModifier)
send(release, cmd)
QApplication.processEvents()
assert count[0] == before
checks.append('Real Command combinations still cancel with empty WebEngine events')

front()
send(press, cmd)
send(release, cmd)
window.reviewer.card = object()
QApplication.processEvents()
assert count[0] == before
checks.append('Deferred reveal checks the card again before acting')

# Confirm the archive contains the intended payload, no QA or cache files.
from zipfile import ZipFile
with ZipFile(source.parent.parent / 'dist' / 'Tap to Flip.ankiaddon') as archive:
    assert set(archive.namelist()) == {'__init__.py','config.json','manifest.json'}
    assert archive.read('__init__.py') == source.read_bytes()
    assert json.loads(archive.read('manifest.json'))['package'] == 'tap_to_flip'
checks.append('Installable archive matches source')
print(json.dumps({'passed': len(checks), 'checks': checks,
    'scope': 'Real Anki bundled PyQt 6.9; isolated window and reviewer stand-in. No live collection or physical key input used.'}, indent=2))
window.close()
