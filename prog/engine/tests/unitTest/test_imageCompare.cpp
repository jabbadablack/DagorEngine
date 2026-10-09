// Copyright (C) Gaijin Games KFT.  All rights reserved.

#include <unittest/dag_unitTest.h>
#include <catch2/catch_approx.hpp>
#include <image/dag_imageCompare.h>
#include <image/dag_texPixel.h>
#include <memory/dag_memBase.h>
#include <EASTL/unique_ptr.h>

namespace
{
struct ImageDeleter
{
  void operator()(TexImage32 *img) const { memfree(img, tmpmem); }
};
using ImagePtr = eastl::unique_ptr<TexImage32, ImageDeleter>;

ImagePtr make_gradient(int w, int h)
{
  ImagePtr img(TexImage32::create(w, h, tmpmem));
  for (int y = 0; y < h; y++)
    for (int x = 0; x < w; x++)
    {
      TexPixel32 &p = img->getPixels()[y * w + x];
      p.r = (unsigned char)(x * 255 / (w - 1));
      p.g = (unsigned char)(y * 255 / (h - 1));
      p.b = 128;
      p.a = 255;
    }
  return img;
}
} // namespace

TEST_CASE("identical images match exactly", "[imageCompare]")
{
  ImagePtr a = make_gradient(16, 8), b = make_gradient(16, 8);
  const ImageCompareResult res = compare_images(*a, *b, ImageCompareParams{});
  CHECK(res.passed);
  CHECK_FALSE(res.sizeMismatch);
  CHECK(res.rms == 0.f);
  CHECK(res.maxChannelDiff == 0);
  CHECK(res.badPixels == 0);
}

TEST_CASE("size mismatch never passes", "[imageCompare]")
{
  ImagePtr a = make_gradient(16, 8), b = make_gradient(8, 16);
  ImageCompareParams params;
  params.maxRms = 255.f;
  params.maxBadPixelsPercent = 100.f;
  const ImageCompareResult res = compare_images(*a, *b, params);
  CHECK_FALSE(res.passed);
  CHECK(res.sizeMismatch);
}

TEST_CASE("per channel tolerance and bad pixel share", "[imageCompare]")
{
  ImagePtr ref = make_gradient(10, 10), act = make_gradient(10, 10);
  act->getPixels()[0].r += 3;  // small difference in one pixel
  act->getPixels()[1].g += 40; // large difference in another

  SECTION("exact comparison reports both pixels")
  {
    const ImageCompareResult res = compare_images(*act, *ref, ImageCompareParams{});
    CHECK_FALSE(res.passed);
    CHECK(res.badPixels == 2);
    CHECK(res.badPixelsPercent == Catch::Approx(2.f));
    CHECK(res.maxChannelDiff == 40);
  }
  SECTION("tolerance hides the small difference only")
  {
    ImageCompareParams params;
    params.perChannelTolerance = 5;
    params.maxRms = 10.f;
    const ImageCompareResult res = compare_images(*act, *ref, params);
    CHECK(res.badPixels == 1);
    CHECK_FALSE(res.passed); // 1% bad pixels exceeds the default 0%
    params.maxBadPixelsPercent = 1.f;
    CHECK(compare_images(*act, *ref, params).passed);
  }
  SECTION("rms limit is independent of the bad pixel limit")
  {
    ImageCompareParams params;
    params.perChannelTolerance = 255;
    params.maxRms = 0.5f;
    const ImageCompareResult res = compare_images(*act, *ref, params);
    CHECK(res.badPixels == 0);
    CHECK(res.rms > 0.5f);
    CHECK_FALSE(res.passed);
  }
}

TEST_CASE("alpha is ignored unless requested", "[imageCompare]")
{
  ImagePtr ref = make_gradient(4, 4), act = make_gradient(4, 4);
  act->getPixels()[5].a = 0;
  CHECK(compare_images(*act, *ref, ImageCompareParams{}).passed);
  ImageCompareParams params;
  params.ignoreAlpha = false;
  CHECK_FALSE(compare_images(*act, *ref, params).passed);
}

TEST_CASE("diff image marks bad pixels red", "[imageCompare]")
{
  ImagePtr ref = make_gradient(4, 4), act = make_gradient(4, 4), diff(TexImage32::create(4, 4, tmpmem));
  act->getPixels()[3].b = 0;
  compare_images(*act, *ref, ImageCompareParams{}, diff.get());
  const TexPixel32 bad = diff->getPixels()[3], good = diff->getPixels()[0];
  CHECK(bad.r >= 128);
  CHECK(bad.g == 0);
  CHECK(bad.b == 0);
  CHECK(good.r == good.g);
  CHECK(good.g == good.b);
}

TEST_CASE("reference image check", "[imageCompare][reference]")
{
  ImagePtr img = make_gradient(16, 8);
  CHECK_IMAGE(*img, "gradient", ImageCompareParams{});

  SECTION("a mismatch fails with a descriptive message")
  {
    img->getPixels()[0].r ^= 0xFF;
    const unittest::ImageCheckResult res = unittest::check_image(*img, "gradient", ImageCompareParams{});
    CHECK_FALSE(res.passed);
    CHECK(strstr(res.message, "differs from reference"));
  }
  SECTION("a missing reference fails")
  {
    const unittest::ImageCheckResult res = unittest::check_image(*img, "no_such_reference", ImageCompareParams{});
    CHECK_FALSE(res.passed);
    CHECK(strstr(res.message, "is missing"));
  }
}
