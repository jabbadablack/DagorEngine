// Copyright (C) Gaijin Games KFT.  All rights reserved.

#include <unittest/dag_unitTest.h>
#include "../webbackend.h"
#include "../webutil.h"
#include <ioSys/dag_dataBlock.h>
#include <osApiWrappers/dag_cpuJobs.h>
#include <osApiWrappers/dag_direct.h>
#include <osApiWrappers/dag_files.h>
#include <osApiWrappers/dag_miscApi.h>
#include <perfMon/dag_cpuFreq.h>
#include <EASTL/unique_ptr.h>
#include <openssl/sha.h>
#include <string.h>
#include <sys/stat.h>
#include <zlib.h>

// The web cache downloads from the HTTP server dng.py test provides (requires:t="http_server" in test.blk, see
// unittest::http_service); without it every case is skipped. Each case serves its own files from a fresh subdir of the
// server root and keeps its cache in its own scratch dir.

namespace
{
const char *const SERVED_FILES[][2] = {
  {"alpha.txt", "datacache web backend: alpha"},
  {"beta.txt", "datacache web backend: beta, a bit longer"},
};
constexpr int PUMP_TIMEOUT_MSEC = 15000;

struct BackendDeleter
{
  void operator()(datacache::Backend *b) const { delete b; }
};
using BackendPtr = eastl::unique_ptr<datacache::Backend, BackendDeleter>;

struct DownloadResult
{
  int calls = 0;
  datacache::ErrorCode err = datacache::ERR_UNKNOWN;
  int size = -1;
  String key;

  static void on_loaded(const char *key, datacache::ErrorCode err, datacache::Entry *entry, void *arg)
  {
    DownloadResult &res = *(DownloadResult *)arg;
    res.calls++;
    res.err = err;
    res.key = key;
    res.size = entry ? entry->getDataSize() : -1;
    if (entry)
      entry->free();
  }
};

void write_file(const char *path, const char *data)
{
  REQUIRE(dd_mkpath(path));
  file_ptr_t f = df_open(path, DF_WRITE | DF_CREATE);
  REQUIRE(f);
  REQUIRE(df_write(f, data, (int)strlen(data)) == (int)strlen(data));
  df_close(f);
}

// 00index.gz lists "<name> <size> <mtime> <sha1>" for every served file
void write_index(const char *dir)
{
  gzFile index = gzopen(String(0, "%s/00index.gz", dir), "wb");
  REQUIRE(index);
  for (const auto &file : SERVED_FILES)
  {
    struct stat st = {};
    REQUIRE(stat(String(0, "%s/%s", dir, file[0]), &st) == 0);
    uint8_t hash[SHA_DIGEST_LENGTH];
    SHA1((const uint8_t *)file[1], strlen(file[1]), hash);
    char hashStr[SHA_DIGEST_LENGTH * 2 + 1];
    gzprintf(index, "%s %d %d %s\n", file[0], (int)strlen(file[1]), (int)st.st_mtime, datacache::hashstr(hash, hashStr));
  }
  gzclose(index);
}

struct WebCacheFixture
{
  String servedUrl, servedDir;
  BackendPtr cache;

  void start(bool index, bool return_stale_data)
  {
    static int caseCounter = 0;
    String baseUrl, root;
    if (!unittest::http_service(baseUrl, root))
      SKIP("no HTTP server (run with dng.py test or set DAGOR_TEST_HTTP_URL and DAGOR_TEST_HTTP_ROOT)");
    const String subdir(0, "webcache%d", ++caseCounter);
    servedUrl.printf(0, "%s%s", baseUrl.c_str(), subdir.c_str());
    servedDir.printf(0, "%s/%s", root.c_str(), subdir.c_str());
    for (const auto &file : SERVED_FILES)
      write_file(String(0, "%s/%s", servedDir.c_str(), file[0]), file[1]);
    if (index)
      write_index(servedDir);

    DataBlock params;
    params.setStr("mountPath", unittest::scratch_dir());
    params.addBlock("baseUrls")->setStr("url", servedUrl);
    params.setBool("allowReturnStaleData", return_stale_data);
    params.setBool("noIndex", !index);
    params.setInt("traceLevel", 0);
    datacache::WebBackendConfig config(params);
    cache.reset(datacache::WebBackend::create(config));
    REQUIRE(cache);
  }

  // polls the cache until all results are delivered, failing on timeout
  void pump(std::initializer_list<const DownloadResult *> results)
  {
    const int start = get_time_msec();
    for (;;)
    {
      bool done = true;
      for (const DownloadResult *res : results)
        done = done && res->calls > 0;
      if (done)
        return;
      if (get_time_msec() - start > PUMP_TIMEOUT_MSEC)
        FAIL("timed out waiting for the web cache");
      cache->poll();
      cpujobs::release_done_jobs();
      sleep_msec(1);
    }
  }

  void check_cached(const char *key, const char *expected_data)
  {
    datacache::EntryHolder entry(cache->get(key)); // without a callback get() only looks into the local cache
    REQUIRE(entry);
    dag::ConstSpan<uint8_t> data = entry->getData();
    REQUIRE(data.size() == strlen(expected_data));
    CHECK(memcmp(data.data(), expected_data, data.size()) == 0);
  }
};
} // namespace

TEST_CASE_METHOD(WebCacheFixture, "web cache downloads indexed files", "[datacache][web][network]")
{
  start(/*index*/ true, /*return_stale_data*/ false);
  for (const auto &file : SERVED_FILES)
  {
    DownloadResult res;
    datacache::ErrorCode err = datacache::ERR_UNKNOWN;
    CHECK(cache->get(file[0], &err, DownloadResult::on_loaded, &res) == nullptr);
    REQUIRE(err == datacache::ERR_PENDING);
    pump({&res});
    CHECK(res.calls == 1);
    CHECK(res.err == datacache::ERR_OK);
    CHECK(res.key == file[0]);
    CHECK(res.size == (int)strlen(file[1]));
    check_cached(file[0], file[1]);
  }
}

TEST_CASE_METHOD(WebCacheFixture, "web cache completes every request for a pending key", "[datacache][web][network]")
{
  start(/*index*/ true, /*return_stale_data*/ false);
  DownloadResult res0, res1;
  datacache::ErrorCode err0 = datacache::ERR_UNKNOWN, err1 = datacache::ERR_UNKNOWN;
  datacache::EntryHolder(cache->get(SERVED_FILES[0][0], &err0, DownloadResult::on_loaded, &res0));
  datacache::EntryHolder(cache->get(SERVED_FILES[0][0], &err1, DownloadResult::on_loaded, &res1));
  CHECK(err0 == datacache::ERR_PENDING);
  CHECK(err1 == datacache::ERR_PENDING);
  pump({&res0, &res1});
  CHECK(res0.err == datacache::ERR_OK);
  CHECK(res1.err == datacache::ERR_OK);
  CHECK(res0.calls == 1);
  CHECK(res1.calls == 1);
}

TEST_CASE_METHOD(WebCacheFixture, "web cache rejects keys missing from the index", "[datacache][web][network]")
{
  start(/*index*/ true, /*return_stale_data*/ false);
  DownloadResult first;
  datacache::EntryHolder(cache->get(SERVED_FILES[0][0], nullptr, DownloadResult::on_loaded, &first));
  pump({&first}); // the index is loaded now
  REQUIRE(first.err == datacache::ERR_OK);

  DownloadResult missing;
  datacache::ErrorCode err = datacache::ERR_OK;
  CHECK(cache->get("not_in_index.txt", &err, DownloadResult::on_loaded, &missing) == nullptr);
  CHECK(err == datacache::ERR_UNKNOWN);
  CHECK(missing.calls == 0); // answered synchronously
}

TEST_CASE_METHOD(WebCacheFixture, "web cache without index downloads urls and keys", "[datacache][web][network]")
{
  start(/*index*/ false, /*return_stale_data*/ true);
  const char *name = SERVED_FILES[1][0], *data = SERVED_FILES[1][1];
  String url(0, "%s/%s", servedUrl.c_str(), name);
  SECTION("absolute url")
  {
    DownloadResult res;
    datacache::ErrorCode err = datacache::ERR_UNKNOWN;
    CHECK(cache->get(url, &err, DownloadResult::on_loaded, &res) == nullptr);
    REQUIRE(err == datacache::ERR_PENDING);
    pump({&res});
    CHECK(res.err == datacache::ERR_OK);
    datacache::EntryHolder entry(cache->get(url));
    REQUIRE(entry);
    CHECK(entry->getDataSize() == (int)strlen(data));
  }
  SECTION("key relative to the base url")
  {
    DownloadResult res;
    datacache::ErrorCode err = datacache::ERR_UNKNOWN;
    cache->get(name, &err, DownloadResult::on_loaded, &res);
    REQUIRE(err == datacache::ERR_PENDING);
    pump({&res});
    CHECK(res.err == datacache::ERR_OK);
    CHECK(res.key == name);
    check_cached(name, data);
  }
}
