// Copyright (C) Gaijin Games KFT. All rights reserved.
#pragma once
// Enforce this on the implementation, while allowing a game's normal build to
// pass source data to the precise library through its public API.
#if defined(__FAST_MATH__) || defined(_M_FP_FAST)
#error CSG implementation requires precise floating-point compilation.
#endif
