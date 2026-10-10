from "%darg/ui_imports.nut" import *

/*
  todo:
    - gather actions by controller and show it like in Apex
    - show contexts ?
    - show gyro
*/
const PS4_CONTROLLER_IMAGE = "!samples_heavy/controller/controller_dualshock4.png"
const XBOX_CONTROLLER_IMAGE = "!samples_heavy/controller/controller_xbox_one.png"
let opts = [XBOX_CONTROLLER_IMAGE, PS4_CONTROLLER_IMAGE]
function controller(image){
  return {
    rendObj=ROBJ_IMAGE
    image = Picture(image)
    keepAspect = true
    size = [pw(50), ph(50)]
    hplace = ALIGN_CENTER
    vplace = ALIGN_CENTER
  }
}
function mkLine(points){
  return {
    rendObj = ROBJ_VECTOR_CANVAS
    size = flex()
    lineWidth = hdpx(1.5)
    color = Color(100,100,100,100)
    commands = [
      [VECTOR_LINE].extend(points),
    ]
  }
}
const rightPoint = 77
const leftPoint = 23

let lines = {
  [XBOX_CONTROLLER_IMAGE] = {
    A_line = {points = [62.6, 55, rightPoint, 55]},
    B_line = {points = [66, 50, rightPoint, 50]},
    Y_line = {points = [62.8, 45, rightPoint, 45]}
    X_line = {points = [58.5,53.5, 58.5,56, 61,60, rightPoint, 60]},
    L_stick ={points = [36, 52, leftPoint, 52]},
    D_pad =  {points = [41,62, 28,62, leftPoint,70, leftPoint,75]},
    LB = {points = [35,37, leftPoint,37]}
    LT = {points = [36.,32, leftPoint,32]}
    RB = {points = [65,37, rightPoint,37]}
    RT = {points = [64,32, rightPoint,32]}
    Back = {points = [47,50, 47,25, leftPoint, 25]}
    Menu = {points = [53,50, 53,25, rightPoint, 25]}
    R_stick ={points = [58,62, 65,70, rightPoint,70]}
  },
  [PS4_CONTROLLER_IMAGE] = {
    CROSS_line = {points = [64.6, 55, rightPoint, 55]},
    CIRCLE_line = {points = [68, 50, rightPoint, 50]},
    TRIANGLE_line = {points = [64.8, 45, rightPoint, 45]}
    SQUARE_line = {points = [60.1,53, 60.1,56, 63,60, rightPoint, 60]},
    L_stick ={points = [41, 62, leftPoint, 62]},
    D_pad =  {points = [36,57, 36,70, leftPoint,70]},
    LB = {points = [34,36, leftPoint,36]}
    LT = {points = [35.5,31, leftPoint,31]}
    RB = {points = [66,36, rightPoint,36]}
    RT = {points = [64.5,31, rightPoint,31]}
    Back = {points = [41.5,40, 41.5,25, leftPoint, 25]}
    Menu = {points = [58.5,40, 58.5,25, rightPoint, 25]}
    R_stick ={points = [58,62, 65,70, rightPoint,70]}
    Touch_pad ={points = [45,40, 45,18, leftPoint, 18]},
  }
}

let curImage = Watched(XBOX_CONTROLLER_IMAGE)
function controller_layout(){
  let vector_lines = lines[curImage.get()].values().map(@(v) mkLine(v.points))
  return {
    watch = curImage
    rendObj=ROBJ_FRAME
    children = [
      controller(curImage.get())
    ].extend(vector_lines)
    size = [sw(50), sh(50)]
  }
}
function switchImages(){
  let cur = opts.indexof(curImage.get())??0
  let next = cur+1 <= opts.len()-1 ? cur+1 : 0
  dlog(next)
  curImage(opts[next])
}
return {
  halign = ALIGN_CENTER
  valign = ALIGN_CENTER
  children = controller_layout
  rendObj = ROBJ_SOLID
  behavior = Behaviors.Button
  onClick = switchImages
  color = Color(0,0,0)
}