from "%darg/ui_imports.nut" import *

import "samples_prog/_cursors.nut" as cursors
import "gamelib.sound" as sound
from "math" import sin, PI

let sndFile = sound.PcmSound("samples_heavy/gamelib/1.wav")

function genSine() {
  const len = 512
  let waveform = array(len, 0.0)
  for (local i=0; i<len; ++i)
    waveform[i] = sin(i*2*PI/256.0)
  return sound.PcmSound({freq=48000, channels=1, data=waveform})
}

let sndSine = genSine()
local sineHandle = Watched(null)

function button(text, handler) {
  return {
    behavior = Behaviors.Button
    rendObj = ROBJ_SOLID
    color = Color(120, 120, 180)
    size = [sh(40), SIZE_TO_CONTENT]
    halign = ALIGN_CENTER
    children = {
      rendObj = ROBJ_TEXT
      text
      padding = sh(2)
    }
    onClick = handler
  }
}

let content = @() {
  size = SIZE_TO_CONTENT
  gap = sh(10)
  watch = sineHandle

  flow = FLOW_VERTICAL
  children = [
    button("Play file", @() sound.play_sound(sndFile))
    button("Play file + octave", @() sound.play_sound(sndFile, {pitch=2.0}))
    button(sineHandle.get()==null ? "Loop sine" : "Stop sine", function() {
      if (sineHandle.get()==null)
        sineHandle(sound.play_sound(sndSine, {loop=true}))
      else {
        sound.stop_sound(sineHandle.get())
        sineHandle(null)
      }
    })
  ]
}


return function() {
  return {
    size = flex()
    rendObj = ROBJ_SOLID
    color = 0xFF202020
    valign = ALIGN_CENTER
    halign = ALIGN_CENTER
    flow = FLOW_VERTICAL
    children = content
    cursor = cursors.normal
  }
}
