//
// Dagor Engine 6.5
// Copyright (C) Gaijin Games KFT.  All rights reserved.
//
#pragma once

struct TexImage32;

// Tolerances for comparing an image against a reference.
// Channel values are compared in [0..255]; defaults require an exact match.
struct ImageCompareParams
{
  int perChannelTolerance = 0;     // a pixel is bad when any compared channel differs by more than this
  float maxRms = 0.f;              // max root-mean-square of channel differences over the whole image
  float maxBadPixelsPercent = 0.f; // max share of bad pixels, in percent
  bool ignoreAlpha = true;
};

struct ImageCompareResult
{
  bool passed = false;
  bool sizeMismatch = false;
  float rms = 0.f;
  int maxChannelDiff = 0;
  int badPixels = 0;
  float badPixelsPercent = 0.f;
};

// Compares actual against reference. When diff_out is not null it must have the reference size and receives a
// visualization: matching pixels as a dimmed grayscale of the reference, bad pixels in red scaled by their difference.
// On size mismatch nothing is compared and diff_out is left untouched.
ImageCompareResult compare_images(const TexImage32 &actual, const TexImage32 &reference, const ImageCompareParams &params,
  TexImage32 *diff_out = nullptr);
