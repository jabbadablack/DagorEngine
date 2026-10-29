#default:forbid-root-table
// The embedded entity editor is the engine's Quirrel/daRg UI.
from "%darg/ui_imports.nut" import *
let editor = require_optional("daEditorEmbedded") != null
  ? require("%daeditor/editor.nut") : null

return @() {
  size = flex()
  children = [
    { rendObj = ROBJ_TEXT text = "@GAME_NAME@ | F2 editor | F10 free camera"
      fontSize = hdpx(20) margin = hdpx(12) color = Color(240, 240, 240) }
    editor
  ]
}
