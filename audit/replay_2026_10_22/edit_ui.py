from pathlib import Path
web = Path(__file__).resolve().parents[2] / 'test-interface-any-start/web'
p = web / 'index.html'
s = p.read_text('utf-8')
needle = '            <button id="reconnect-button"'
assert s.count(needle) == 1
s = s.replace(needle, '''            <div class="replay-toolbar"><span id="replay-status" role="status" hidden></span><button id="replay-button" class="text-button" type="button" disabled data-i18n="replay">Odtwórz rundę</button></div>
            <p id="replay-summary" class="replay-summary" hidden></p>
''' + needle)
needle = '<pre id="details-json">'
assert s.count(needle) == 1
s = s.replace(needle, '<button id="details-replay-button" class="secondary-button" type="button" data-i18n="replay">Odtwórz rundę</button>' + needle)
p.write_text(s, 'utf-8')
p = web / 'game-layout.js'
s = p.read_text('utf-8')
s = s.replace('  if (studio) settings.append(document.querySelector(".history-section"));\n  else document.querySelector(".history-section").hidden = true;', '  settings.append(document.querySelector(".history-section"));')
p.write_text(s, 'utf-8')
