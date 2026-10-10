// Copyright (C) Gaijin Games KFT.  All rights reserved.

#include <unittest/dag_unitTest.h>
#include <streamIO/streamIO.h>
#include <ioSys/dag_genIo.h>
#include <osApiWrappers/dag_cpuJobs.h>
#include <osApiWrappers/dag_directUtils.h>
#include <osApiWrappers/dag_miscApi.h>
#include <EASTL/unique_ptr.h>
#include <sys/stat.h>
#include <stdlib.h>
#include <string.h>

// HTTP cases use the server dng.py test provides (requires:t="http_server" in test.blk, see unittest::http_service);
// without it they are skipped.

static constexpr const char *SAMPLE_FILE = "data/sample.txt";
static constexpr const char *SAMPLE_PREFIX = "streamIO test data: ";

namespace
{
struct StreamResult
{
  int err = -1;
  eastl::unique_ptr<IGenLoad> load;
  int64_t lastModified = -1;
};

struct StreamFixture
{
  eastl::unique_ptr<streamio::Context> ctx{streamio::create()};

  StreamResult open(const char *url, int64_t modified_since = -1)
  {
    struct Pending
    {
      StreamResult res;
      volatile bool done = false;
    } pending;
    ctx->createStream(
      url,
      [](const char *, int err, IGenLoad *load, void *arg, int64_t last_modified, intptr_t) {
        Pending &p = *(Pending *)arg;
        p.res.err = err;
        p.res.load.reset(load);
        p.res.lastModified = last_modified;
        p.done = true;
      },
      nullptr, nullptr, nullptr, &pending, modified_since);
    while (!pending.done)
    {
      sleep_msec(1);
      cpujobs::release_done_jobs();
      ctx->poll();
    }
    return eastl::move(pending.res);
  }
};

void check_sample(const StreamResult &res)
{
  REQUIRE(res.err == 0);
  REQUIRE(res.load.get() != nullptr);
  char buf[40] = {};
  CHECK(res.load->tryRead(buf, sizeof(buf) - 1) == sizeof(buf) - 1);
  CHECK(strncmp(buf, SAMPLE_PREFIX, strlen(SAMPLE_PREFIX)) == 0);
}

// Serves a copy of the sample file and returns {url of the copy, local path of the copy}; skips without a server.
struct ServedSample
{
  String url, path;
};
ServedSample serve_sample()
{
  String baseUrl, root;
  if (!unittest::http_service(baseUrl, root))
    SKIP("no HTTP server (run with dng.py test or set DAGOR_TEST_HTTP_URL and DAGOR_TEST_HTTP_ROOT)");
  ServedSample s{String(0, "%ssample.txt", baseUrl.c_str()), String(0, "%s/sample.txt", root.c_str())};
  REQUIRE(dag::copy_file(unittest::data_path(SAMPLE_FILE), s.path));
  return s;
}

int64_t file_mtime(const char *path)
{
  struct stat st = {};
  REQUIRE(stat(path, &st) == 0);
  return int64_t(st.st_mtime);
}
} // namespace

TEST_CASE_METHOD(StreamFixture, "streamIO reads a local file", "[streamIO]") { check_sample(open(unittest::data_path(SAMPLE_FILE))); }

TEST_CASE_METHOD(StreamFixture, "streamIO reports a missing local file", "[streamIO]")
{
  const StreamResult res = open(unittest::data_path("data/no_such_file.txt"));
  CHECK(res.err != 0);
  CHECK(res.load.get() == nullptr);
}

TEST_CASE_METHOD(StreamFixture, "streamIO reads over http", "[streamIO][network]") { check_sample(open(serve_sample().url)); }

TEST_CASE_METHOD(StreamFixture, "streamIO reports a missing http resource", "[streamIO][network]")
{
  const ServedSample sample = serve_sample();
  const StreamResult res = open(String(0, "%s.missing", sample.url.c_str()));
  CHECK(res.err != 0);
  CHECK(res.load.get() == nullptr);
}

// response headers (and so Last-Modified) are only requested together with If-Modified-Since
TEST_CASE_METHOD(StreamFixture, "streamIO returns the http last modified time", "[streamIO][network]")
{
  const ServedSample sample = serve_sample();
  const StreamResult res = open(sample.url, /*modified_since*/ 0);
  REQUIRE(res.err == 0);
  CHECK(res.lastModified == file_mtime(sample.path));
}

TEST_CASE_METHOD(StreamFixture, "streamIO honours If-Modified-Since", "[streamIO][network]")
{
  const ServedSample sample = serve_sample();
  const StreamResult res = open(sample.url, file_mtime(sample.path));
  CHECK(res.err == streamio::ERR_NOT_MODIFIED);
  CHECK(res.load.get() == nullptr);
}
