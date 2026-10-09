// Copyright (C) Gaijin Games KFT.  All rights reserved.

#include <image/dag_imageCompare.h>
#include <image/dag_texPixel.h>
#include <math/dag_mathBase.h>
#include <util/dag_globDef.h>

ImageCompareResult compare_images(const TexImage32 &actual, const TexImage32 &reference, const ImageCompareParams &params,
  TexImage32 *diff_out)
{
  ImageCompareResult res;
  if (actual.w != reference.w || actual.h != reference.h)
  {
    res.sizeMismatch = true;
    return res;
  }
  G_ASSERT(!diff_out || (diff_out->w == reference.w && diff_out->h == reference.h));

  const int pixelCount = reference.w * reference.h;
  const int channels = params.ignoreAlpha ? 3 : 4;
  const TexPixel32 *a = actual.getPixels();
  const TexPixel32 *r = reference.getPixels();
  TexPixel32 *d = diff_out ? diff_out->getPixels() : nullptr;
  double sqSum = 0;
  for (int i = 0; i < pixelCount; i++)
  {
    const int db = abs(int(a[i].b) - int(r[i].b));
    const int dg = abs(int(a[i].g) - int(r[i].g));
    const int dr = abs(int(a[i].r) - int(r[i].r));
    const int da = params.ignoreAlpha ? 0 : abs(int(a[i].a) - int(r[i].a));
    const int pixelMax = max(max(db, dg), max(dr, da));
    sqSum += db * db + dg * dg + dr * dr + da * da;
    res.maxChannelDiff = max(res.maxChannelDiff, pixelMax);
    const bool bad = pixelMax > params.perChannelTolerance;
    if (bad)
      res.badPixels++;
    if (d)
    {
      if (bad)
      {
        d[i].r = (unsigned char)min(255, 128 + pixelMax);
        d[i].g = d[i].b = 0;
      }
      else
        d[i].r = d[i].g = d[i].b = (unsigned char)((int(r[i].r) * 77 + int(r[i].g) * 150 + int(r[i].b) * 29) >> 9);
      d[i].a = 255;
    }
  }

  res.rms = pixelCount ? float(sqrt(sqSum / (double(pixelCount) * channels))) : 0.f;
  res.badPixelsPercent = pixelCount ? 100.f * res.badPixels / pixelCount : 0.f;
  res.passed = res.rms <= params.maxRms && res.badPixelsPercent <= params.maxBadPixelsPercent;
  return res;
}
