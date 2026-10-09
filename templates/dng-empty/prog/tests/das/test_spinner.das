options gen2
require dastest/testing_boost public
require math
require dng_empty.spinner

// python ../../../project.py test -k dng_empty.das

def close(a, b : float3) : bool {
  return length(a - b) < 1e-5
}

[test]
def rotate_around_up_turns_the_x_axis(t : T?) {
  t |> success(close(rotate_around_up(float3(1, 0, 0), PI * 0.5), float3(0, 0, -1)), "a quarter turn")
  t |> success(close(rotate_around_up(float3(1, 0, 0), PI), float3(-1, 0, 0)), "half a turn")
}

[test]
def rotate_around_up_keeps_up_and_length(t : T?) {
  let v = float3(3, 4, 5)
  let r = rotate_around_up(v, 1.234)
  t |> success(abs(length(r) - length(v)) < 1e-5, "length")
  t |> numericEqual(r.y, v.y, "height")
}
