// Copyright (C) Gaijin Games KFT.  All rights reserved.

#include <unittest/dag_unitTest.h>
#include "../filebackend.h"
#include <ioSys/dag_dataBlock.h>
#include <ioSys/dag_genIo.h>
#include <osApiWrappers/dag_direct.h>
#include <osApiWrappers/dag_files.h>
#include <osApiWrappers/dag_miscApi.h>
#include <EASTL/unique_ptr.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>

// Every case works in its own empty scratch dir (unittest::scratch_dir), so cases neither depend on each other nor on
// the current dir.
//
// A cache with maxSize = 0 (unlimited) never scans its directory: it only knows the entries it was asked for. A size
// limited cache scans on creation (that's where enumeration and garbage removal happen), see FileBackend::create.

namespace
{
const char SAMPLE_KEY[] = "sample.txt";
const char SAMPLE_DATA[] = "datacache file backend sample";
const int64_t SCANNED = 1 << 30; // a size limit large enough to never evict, just to make the cache scan its dir

String join(const char *dir, const char *rel) { return String(0, "%s/%s", dir, rel); }

void write_file(const char *path, const void *data, int size)
{
  REQUIRE(dd_mkpath(path));
  file_ptr_t f = df_open(path, DF_WRITE | DF_CREATE);
  REQUIRE(f);
  REQUIRE(df_write(f, data, size) == size);
  df_close(f);
}

void write_zeros(const char *path, int size)
{
  eastl::unique_ptr<char[]> zeros(new char[size]());
  write_file(path, zeros.get(), size);
}

bool file_exists(const char *path)
{
  struct stat st = {};
  return stat(path, &st) == 0;
}

void wait_next_second(time_t since)
{
  while (time(nullptr) == since)
    sleep_msec(1);
}

struct BackendDeleter
{
  void operator()(datacache::Backend *b) const { delete b; }
};
using BackendPtr = eastl::unique_ptr<datacache::Backend, BackendDeleter>;

BackendPtr create_cache(const char *mount_path, int64_t max_size = 0, const char *ro_mount_path = nullptr)
{
  DataBlock params;
  params.setStr("mountPath", mount_path);
  if (ro_mount_path)
    params.setStr("roMountPath", ro_mount_path);
  params.setInt64("maxSize", max_size);
  params.setInt("traceLevel", 0);
  BackendPtr cache(datacache::FileBackend::create(params));
  REQUIRE(cache);
  return cache;
}

struct CacheFixture
{
  String dir = unittest::scratch_dir();
  BackendPtr cache;

  CacheFixture()
  {
    write_file(join(dir, SAMPLE_KEY), SAMPLE_DATA, sizeof(SAMPLE_DATA) - 1);
    write_file(join(dir, "other.txt"), "other", 5);
    cache = create_cache(dir);
  }
  String path(const char *rel) const { return join(dir, rel); }
};
} // namespace

TEST_CASE_METHOD(CacheFixture, "file cache enumerates every file", "[datacache][file]")
{
  write_zeros(path("subdir/nested.bin"), 16);
  cache = create_cache(dir, SCANNED);
  void *iter = nullptr;
  int count = 0;
  for (datacache::EntryHolder e(cache->nextEntry(&iter)); e; e.reset(cache->nextEntry(&iter)))
    ++count;
  cache->endEnumeration(&iter);
  CHECK(count == 3);
}

TEST_CASE_METHOD(CacheFixture, "file cache hit and miss", "[datacache][file]")
{
  datacache::EntryHolder hit(cache->get(SAMPLE_KEY));
  REQUIRE(hit);
  CHECK(strcmp(hit->getKey(), SAMPLE_KEY) == 0);
  CHECK(cache->get("no_such_key") == nullptr);
}

TEST_CASE_METHOD(CacheFixture, "file cache maps and reads entry data", "[datacache][file]")
{
  datacache::EntryHolder entry(cache->get(SAMPLE_KEY));
  REQUIRE(entry);
  CHECK(entry->getDataSize() == int(sizeof(SAMPLE_DATA) - 1));
  SECTION("mapped data") // an entry has one stream at a time: mapped or read
  {
    dag::ConstSpan<uint8_t> data = entry->getData();
    REQUIRE(data.size() == sizeof(SAMPLE_DATA) - 1);
    CHECK(memcmp(data.data(), SAMPLE_DATA, data.size()) == 0);
  }
  SECTION("read stream")
  {
    IGenLoad *stream = entry->getReadStream();
    REQUIRE(stream != nullptr);
    char buf[sizeof(SAMPLE_DATA) - 1];
    CHECK(stream->tryRead(buf, sizeof(buf)) == sizeof(buf));
    CHECK(memcmp(buf, SAMPLE_DATA, sizeof(buf)) == 0);
  }
}

TEST_CASE_METHOD(CacheFixture, "file cache sets the modification time", "[datacache][file]")
{
  datacache::EntryHolder(cache->set("test.bin", 100500))->getWriteStream();
  struct stat st = {};
  REQUIRE(stat(path("test.bin"), &st) == 0);
  CHECK(st.st_mtime == 100500);
  CHECK(cache->del("test.bin"));
  CHECK_FALSE(file_exists(path("test.bin")));
}

TEST_CASE_METHOD(CacheFixture, "file cache keys may contain directories", "[datacache][file]")
{
  const char *key = "subdir/test.bin";
  datacache::EntryHolder(cache->set(key))->getWriteStream();
  datacache::Entry *entry = cache->get(key);
  REQUIRE(entry);
  entry->del();
  entry->free();
  CHECK_FALSE(file_exists(path(key)));
  CHECK(dd_rmdir(path("subdir"))); // the dir is left empty
}

TEST_CASE_METHOD(CacheFixture, "file cache enumerates keys in directories", "[datacache][file]")
{
  const char *key = "subdir/test.bin";
  write_zeros(path(key), 1);
  cache = create_cache(dir, SCANNED);
  void *iter = nullptr;
  bool found = false;
  while (datacache::Entry *entry = cache->nextEntry(&iter))
  {
    found = strcmp(entry->getKey(), key) == 0;
    entry->free();
    if (found)
      break;
  }
  cache->endEnumeration(&iter);
  CHECK(found);
}

// leftovers of interrupted writes (FileBackend::tmpFilePref) are removed by the directory scan
TEST_CASE_METHOD(CacheFixture, "file cache removes temp files when it scans", "[datacache][file]")
{
  const String garbage = path(".#test.bin");
  write_zeros(garbage, 1);
  SECTION("an unlimited cache does not scan")
  {
    cache = create_cache(dir);
    CHECK(file_exists(garbage));
  }
  SECTION("a size limited cache scans on creation")
  {
    cache = create_cache(dir, SCANNED);
    CHECK_FALSE(file_exists(garbage));
    CHECK(cache->getEntriesCount() == 2); // the temp file is not an entry
  }
}

TEST_CASE_METHOD(CacheFixture, "file cache entry holders", "[datacache][file]")
{
  SECTION("getting the same key twice")
  {
    // get() returns the same ref-counted entry, so each reference needs its own holder: resetting a holder to the pointer
    // it already owns (EntryHolder is a unique_ptr) would skip free() and leak a reference
    datacache::EntryHolder ent1(cache->get(SAMPLE_KEY));
    datacache::EntryHolder ent2(cache->get(SAMPLE_KEY));
    CHECK(ent1.get() == ent2.get());
  }
  SECTION("assigning another holder")
  {
    datacache::EntryHolder ent1(cache->get(SAMPLE_KEY));
    datacache::EntryHolder ent2(cache->get("other.txt"));
    ent1 = eastl::move(ent2);
    CHECK(strcmp(ent1->getKey(), "other.txt") == 0);
  }
  SECTION("an entry outlives populate")
  {
    datacache::EntryHolder entry(cache->get(SAMPLE_KEY));
    cache->getEntriesCount(); // implicit populate
    CHECK(strcmp(entry->getKey(), SAMPLE_KEY) == 0);
  }
}

TEST_CASE_METHOD(CacheFixture, "file cache deletes an entry on its last release", "[datacache][file]")
{
  const char *key = "test.bin";
  write_zeros(path(key), 1);
  cache = create_cache(dir);
  bool populate = false;
  SECTION("linked entry") {}
  SECTION("entry unlinked by populate") { populate = true; }

  datacache::Entry *e1 = cache->get(key);
  REQUIRE(e1);
  e1->del();
  datacache::Entry *e2 = cache->get(key);
  if (populate)
    cache->getEntriesCount();
  e1->free();
  CHECK(file_exists(path(key))); // still referenced by e2
  e2->free();
  CHECK_FALSE(file_exists(path(key)));
}

namespace
{
struct EvictionFixture
{
  String dir = unittest::scratch_dir();
  BackendPtr cache;

  EvictionFixture(int64_t max_size, bool distinct_first_mtime)
  {
    const time_t start = time(nullptr);
    for (int i = 1; i <= 4; ++i)
    {
      write_zeros(String(0, "%s/%d.bin", dir.c_str(), i), 1024);
      if (i == 1 && distinct_first_mtime)
        wait_next_second(start); // make 1.bin strictly the oldest
    }
    cache = create_cache(dir, max_size);
  }
};
} // namespace

TEST_CASE("file cache evicts the oldest entry on write", "[datacache][file][eviction]")
{
  EvictionFixture f(5 << 10, true);
  char dummy[1536] = {};
  CHECK(f.cache->getEntriesCount() == 4);
  datacache::EntryHolder(f.cache->set("subdir/5.bin"))->getWriteStream()->write(dummy, sizeof(dummy));
  CHECK(f.cache->get("1.bin") == nullptr); // evicted
  CHECK(f.cache->getEntriesCount() == 4);
  datacache::EntryHolder(f.cache->set("subdir/6.bin"))->getWriteStream()->write(dummy, 512); // fits, nothing evicted
  CHECK(f.cache->getEntriesCount() == 5);
}

TEST_CASE("file cache frees space on delete", "[datacache][file][eviction]")
{
  EvictionFixture f(4 << 10, false);
  char dummy[1024] = {};
  CHECK(f.cache->getEntriesCount() == 4);
  datacache::EntryHolder(f.cache->get("1.bin"))->del();
  CHECK(f.cache->getEntriesCount() == 3);
  datacache::EntryHolder(f.cache->set("subdir/5.bin"))->getWriteStream()->write(dummy, sizeof(dummy)); // fits after delete
  CHECK(f.cache->getEntriesCount() == 4);
}

namespace
{
struct RoMountFixture
{
  String dir = unittest::scratch_dir();
  String roDir = join(dir, "romount"), rwDir = join(dir, "rw");
  BackendPtr cache;

  explicit RoMountFixture(bool newer_rw_copy = false)
  {
    const time_t start = time(nullptr);
    write_zeros(join(roDir, "1.bin"), 1024);
    if (newer_rw_copy)
    {
      wait_next_second(start);
      write_zeros(join(rwDir, "1.bin"), 512);
    }
    cache = create_cache(rwDir, 0, roDir);
  }
};
} // namespace

TEST_CASE("file cache reads from a read-only mount", "[datacache][file][romount]")
{
  RoMountFixture f;
  datacache::EntryHolder ent(f.cache->get("1.bin"));
  CHECK(ent);
}

TEST_CASE("file cache writes beside a read-only mount", "[datacache][file][romount]")
{
  RoMountFixture f;
  datacache::EntryHolder ent1(f.cache->get("1.bin"));
  datacache::EntryHolder ent2(f.cache->set("1.bin"));
  CHECK(ent1.get() != ent2.get());
}

TEST_CASE("file cache refuses to write a read-only entry", "[datacache][file][romount]")
{
#if DAGOR_DBGLEVEL < 1
  SKIP("the refusal is an assertion, compiled out with DAGOR_DBGLEVEL < 1");
#endif
  RoMountFixture f;
  datacache::EntryHolder ent(f.cache->get("1.bin"));
  REQUIRE(ent);
  unittest::ExpectLogerr expect("Attempt to write in read-only directory");
  CHECK(ent->getWriteStream() == nullptr);
}

TEST_CASE("file cache prefers a newer writable copy over the read-only mount", "[datacache][file][romount]")
{
  RoMountFixture f(/*newer_rw_copy*/ true);
  SECTION("single get") {}
  SECTION("get after populate") { f.cache->getEntriesCount(); }
  datacache::EntryHolder ent(f.cache->get("1.bin"));
  REQUIRE(ent);
  CHECK(ent->getDataSize() == 512);
}
