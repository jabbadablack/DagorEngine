options gen2
options indenting = 2
module spinner shared public

require math

//! Spinner math: pure functions, used by es/spinner_es.das and unit tested without the game (prog/tests/das)

def rotate_around_up(v : float3; angle : float) : float3 {
  //! v turned by angle radians around the up (y) axis
  let s = sin(angle)
  let c = cos(angle)
  return float3(v.x * c + v.z * s, v.y, v.z * c - v.x * s)
}
