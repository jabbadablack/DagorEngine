// Copyright (C) Gaijin Games KFT.  All rights reserved.

#include <unittest/dag_testEnv.h>
#include <image/dag_loadImage.h>
#include <image/dag_png.h>
#include <image/dag_texPixel.h>
#include <memory/dag_memBase.h>
#include <osApiWrappers/dag_direct.h>
#include <osApiWrappers/dag_directUtils.h>

namespace unittest
{
struct TexImage32Holder
{
  TexImage32 *img = nullptr;
  explicit TexImage32Holder(TexImage32 *i) : img(i) {}
  ~TexImage32Holder()
  {
    if (img)
      memfree(img, tmpmem);
  }
  TexImage32Holder(const TexImage32Holder &) = delete;
  TexImage32Holder &operator=(const TexImage32Holder &) = delete;
};

static bool save_image(const char *fn, const TexImage32 &img)
{
  return dd_mkpath(fn) && save_png32(fn, img.getPixels(), img.w, img.h, img.w * sizeof(TexPixel32), nullptr, 0, true);
}

static String find_reference(const char *name)
{
  if (!options().imageVariant.empty())
  {
    String fn = data_path(String(0, "references/%s.%s.png", name, options().imageVariant.c_str()));
    if (dd_file_exists(fn))
      return fn;
  }
  String fn = data_path(String(0, "references/%s.png", name));
  return dd_file_exists(fn) ? fn : String();
}

static void record_event(const char *name, const ImageCheckResult &res, const String &actual, const String &reference,
  const String &diff)
{
  write_event(String(0,
    "\"event\":\"image\",\"case\":\"%s\",\"name\":\"%s\",\"passed\":%s,\"actual\":\"%s\",\"reference\":\"%s\","
    "\"diff\":\"%s\",\"rms\":%g,\"maxChannelDiff\":%d,\"badPixelsPercent\":%g,\"message\":\"%s\"",
    json_escape(current_case()).c_str(), json_escape(name).c_str(), res.passed ? "true" : "false", json_escape(actual).c_str(),
    json_escape(reference).c_str(), json_escape(diff).c_str(), res.compare.rms, res.compare.maxChannelDiff,
    res.compare.badPixelsPercent, json_escape(res.message).c_str()));
}

ImageCheckResult check_image(const TexImage32 &actual, const char *name, const ImageCompareParams &params)
{
  ImageCheckResult res;
  const String actualFn = artifact_path(String(0, "%s.actual.png", name));
  if (!actualFn.empty() && !save_image(actualFn, actual))
    res.message.printf(0, "cannot write %s; ", actualFn.c_str());

  const String refFn = find_reference(name);
  if (refFn.empty())
  {
    if (options().updateReferences)
    {
      const String newRefFn = data_path(String(0, "references/%s.png", name));
      res.passed = save_image(newRefFn, actual);
      if (!res.passed)
        res.message.aprintf(0, "cannot create reference %s", newRefFn.c_str());
      record_event(name, res, actualFn, newRefFn, String());
      return res;
    }
    res.message.aprintf(0, "reference image references/%s.png is missing in %s (rerun with --update-references to create it)", name,
      options().dataDir.c_str());
    record_event(name, res, actualFn, String(), String());
    return res;
  }

  TexImage32Holder ref(load_png32(refFn, tmpmem));
  if (!ref.img)
  {
    res.message.aprintf(0, "cannot load reference %s", refFn.c_str());
    record_event(name, res, actualFn, refFn, String());
    return res;
  }

  const String refCopyFn = artifact_path(String(0, "%s.reference.png", name));
  if (!refCopyFn.empty())
    copy_file(refFn, refCopyFn);

  TexImage32Holder diff(TexImage32::create(ref.img->w, ref.img->h, tmpmem));
  res.compare = compare_images(actual, *ref.img, params, diff.img);
  String diffFn;
  if (!res.compare.sizeMismatch && !res.compare.passed && (diffFn = artifact_path(String(0, "%s.diff.png", name))).length())
    save_image(diffFn, *diff.img);

  if (res.compare.passed)
    res.passed = true;
  else if (options().updateReferences)
  {
    res.passed = save_image(refFn, actual);
    if (!res.passed)
      res.message.aprintf(0, "cannot update reference %s", refFn.c_str());
  }
  else if (res.compare.sizeMismatch)
    res.message.aprintf(0, "image '%s' size %dx%d differs from reference %dx%d (%s)", name, actual.w, actual.h, ref.img->w, ref.img->h,
      refFn.c_str());
  else
    res.message.aprintf(0,
      "image '%s' differs from reference %s: rms=%.3f (max %.3f), bad pixels=%.3f%% (max %.3f%%, tolerance %d), max diff=%d", name,
      refFn.c_str(), res.compare.rms, params.maxRms, res.compare.badPixelsPercent, params.maxBadPixelsPercent,
      params.perChannelTolerance, res.compare.maxChannelDiff);

  record_event(name, res, actualFn, refCopyFn.empty() ? refFn : refCopyFn, diffFn);
  return res;
}

ImageCheckResult check_image_file(const char *actual_fn, const char *name, const ImageCompareParams &params)
{
  TexImage32Holder actual(load_image(actual_fn, tmpmem));
  if (!actual.img)
  {
    ImageCheckResult res;
    res.message.printf(0, "cannot load image %s", actual_fn);
    record_event(name, res, String(actual_fn), String(), String());
    return res;
  }
  return check_image(*actual.img, name, params);
}
} // namespace unittest
