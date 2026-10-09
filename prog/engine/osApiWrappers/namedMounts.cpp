// Copyright (C) Gaijin Games KFT.  All rights reserved.

#include <osApiWrappers/dag_basePath.h>
#include <osApiWrappers/dag_atomic.h>
#include <osApiWrappers/dag_direct.h>
#include <osApiWrappers/dag_files.h>
#include <osApiWrappers/dag_rwLock.h>
#include <EASTL/hash_map.h>
#include <EASTL/string.h>
#include <dag/dag_vector.h>
#include <generic/dag_sort.h>
#include <supp/dag_alloca.h>
#include <debug/dag_debug.h>
#include <stdlib.h>
#if _TARGET_PC_WIN
#include <direct.h>
#define getcwd _getcwd
#else
#include <unistd.h>
#endif

static eastl::hash_map<eastl::string, eastl::string> named_mounts; // Note: intentionally no ska, since we return pointers to string
                                                                   // data
static OSReadWriteLock named_mounts_rwlock;

void dd_set_named_mount_path(const char *mount_name, const char *path_to)
{
  if (mount_name[0] == '%')
    mount_name++;
  eastl::string chained;
  if (path_to && *path_to == '%') // chained mount (%engine/prog/x): stored resolved, as a plain path
  {
    const char *mntPath = nullptr;
    const char *rest = dd_resolve_named_mount_in_path(path_to, mntPath);
    if (rest != path_to)
    {
      chained.sprintf("%s%s", mntPath, rest);
      path_to = chained.c_str();
    }
  }
  if (path_to)
  {
    G_ASSERTF_RETURN(strlen(mount_name) < MAX_MOUNT_NAME_LEN, , "too long mount_name=%s", mount_name);
    for (const char *m = mount_name; *m; m++)
      G_ASSERTF_RETURN((*m >= 'a' && *m <= 'z') || (*m >= 'A' && *m <= 'Z') || (*m >= '0' && *m <= '9') || *m == '_', ,
        "invalid mount_name=%s", mount_name);
    if (*path_to == '.' && *(path_to + 1) == '\0')
      path_to = "";

    size_t len = strlen(path_to);
    while (len > 0 && (path_to[len - 1] == '/' || path_to[len - 1] == '\\'))
      len--;
    ScopedLockWriteTemplate<OSReadWriteLock> lock(named_mounts_rwlock);
    named_mounts[mount_name] = eastl::string_view(path_to, len);
  }
  else
  {
    ScopedLockWriteTemplate<OSReadWriteLock> lock(named_mounts_rwlock);
    auto it = named_mounts.find_as(mount_name);
    if (it != named_mounts.end())
      named_mounts.erase(it);
  }
}

const char *dd_get_named_mount_by_path(const char *fpath)
{
  ScopedLockReadTemplate<OSReadWriteLock> lock(named_mounts_rwlock);
  for (auto &it : named_mounts)
  {
    if (strncmp(fpath, it.second.c_str(), it.second.size()) == 0)
      return it.first.c_str();
  }
  return nullptr;
}

static const char *find_named_mount(const char *mount_name)
{
  ScopedLockReadTemplate<OSReadWriteLock> lock(named_mounts_rwlock);
  auto it = named_mounts.find_as(mount_name);
  return (it != named_mounts.end()) ? it->second.c_str() : nullptr;
}

static bool is_abs_path(const char *p) { return p[0] == '/' || p[0] == '\\' || (p[0] && p[1] == ':'); }

// engine.blk of a game project: engineRoot:t="<engine root, absolute or relative to the dir of engine.blk>"
static bool read_engine_blk(const char *dir, eastl::string &out_root)
{
  const eastl::string fn(eastl::string::CtorSprintf(), "%s/engine.blk", dir);
  file_ptr_t f = df_open(fn.c_str(), DF_READ | DF_IGNORE_MISSING | DF_REALFILE_ONLY);
  if (!f)
    return false;
  char buf[4096];
  const int len = df_read(f, buf, sizeof(buf) - 1);
  df_close(f);
  buf[len > 0 ? len : 0] = '\0';
  const char *key = strstr(buf, "engineRoot");
  const char *open = key ? strchr(key, '"') : nullptr;
  const char *close = open ? strchr(open + 1, '"') : nullptr;
  if (!close)
  {
    logerr("%s: expected engineRoot:t=\"<engine root>\"", fn.c_str());
    return false;
  }
  const eastl::string root(open + 1, close);
  out_root = is_abs_path(root.c_str()) ? root : eastl::string(eastl::string::CtorSprintf(), "%s/%s", dir, root.c_str());
  return true;
}

static bool detect_engine_root(eastl::string &out_root, const char *&out_source)
{
  if (const char *env = getenv("DAGOR_ENGINE_ROOT"); env && *env)
  {
    out_root = env;
    out_source = "DAGOR_ENGINE_ROOT";
    return true;
  }
  char dir[DAGOR_MAX_PATH];
  if (!getcwd(dir, sizeof(dir)))
    return false;
  for (char *c = dir; *c; c++)
    if (*c == '\\')
      *c = '/';
  for (;;)
  {
    if (read_engine_blk(dir, out_root))
    {
      out_source = "engine.blk";
      return true;
    }
    if (dd_file_exist(eastl::string(eastl::string::CtorSprintf(), "%s/prog/_jBuild/defaults.jam", dir).c_str()))
    {
      out_root = dir;
      out_source = "engine checkout";
      return true;
    }
    char *slash = strrchr(dir, '/');
    if (!slash || slash == dir || (slash == dir + 2 && dir[1] == ':'))
      return false;
    *slash = '\0';
  }
}

static const char *const ENGINE_MOUNT = "engine";

static const char *detect_engine_mount()
{
  static volatile int detected = 0;
  if (interlocked_exchange(detected, 1)) // once per process; an explicit dd_set_named_mount_path() always wins
    return find_named_mount(ENGINE_MOUNT);
  eastl::string root;
  const char *source = "";
  if (!detect_engine_root(root, source))
  {
    logwarn("named mount %%%s is not set: no DAGOR_ENGINE_ROOT, no engine.blk or engine checkout above the current dir", ENGINE_MOUNT);
    return nullptr;
  }
  char simplified[DAGOR_MAX_PATH];
  strncpy(simplified, root.c_str(), sizeof(simplified) - 1);
  simplified[sizeof(simplified) - 1] = '\0';
  dd_simplify_fname_c(simplified);
  if (!find_named_mount(ENGINE_MOUNT))
  {
    dd_set_named_mount_path(ENGINE_MOUNT, simplified);
    debug("named mount %%%s = %s (from %s)", ENGINE_MOUNT, simplified, source);
  }
  return find_named_mount(ENGINE_MOUNT);
}

const char *dd_get_named_mount_path(const char *mount_name, int mount_name_len)
{
  if (mount_name_len >= 0 && mount_name[mount_name_len])
  {
    char *p = (char *)alloca(mount_name_len + 1);
    memcpy(p, mount_name, mount_name_len);
    p[mount_name_len] = '\0';
    mount_name = p;
  }
  if (const char *path = find_named_mount(mount_name))
    return path;
  return strcmp(mount_name, ENGINE_MOUNT) == 0 ? detect_engine_mount() : nullptr;
}

bool dd_check_named_mount_in_path_valid(const char *fpath)
{
  if (fpath && *fpath == '%')
  {
    if (const char *p = strchr(fpath + 1, '/'))
      return dd_get_named_mount_path(fpath + 1, p - fpath - 1) != nullptr;
    else
      return dd_get_named_mount_path(fpath + 1) != nullptr;
  }
  return true;
}

const char *dd_resolve_named_mount_in_path(const char *fpath, const char *&mnt_path)
{
  if (fpath && *fpath == '%')
  {
    if (const char *p = strchr(fpath + 1, '/'))
    {
      if ((mnt_path = dd_get_named_mount_path(fpath + 1, p - fpath - 1)) != nullptr)
        return *mnt_path ? p : p + 1;
      logerr("named mount <%.*s> not set for %s", p - fpath - 1, fpath + 1, fpath);
    }
    else
    {
      if ((mnt_path = dd_get_named_mount_path(fpath + 1)) != nullptr)
        return "";
      logerr("named mount <%s> not set", fpath + 1);
    }
  }
  mnt_path = "";
  return fpath;
}

void dd_dump_named_mounts()
{
  ScopedLockReadTemplate<OSReadWriteLock> lock(named_mounts_rwlock);
#if DAGOR_DBGLEVEL > 0 || DAGOR_FORCE_LOGS
  debug("registered %d named mount(s)%s", named_mounts.size(), named_mounts.size() > 0 ? ":" : "");
  typedef eastl::pair<const char *, const char *> str_pair;
  dag::Vector<str_pair> sorted_mounts;
  sorted_mounts.reserve(named_mounts.size());
  for (auto &it : named_mounts)
    sorted_mounts.push_back({it.first.c_str(), it.second.c_str()});
  stlsort::sort(sorted_mounts.begin(), sorted_mounts.end(),
    [](const str_pair &a, const str_pair &b) { return strcmp(a.first, b.first) < 0; });
  for (auto &it : sorted_mounts)
    debug("  %%%s = %s", it.first, it.second);
#endif
}

#define EXPORT_PULL dll_pull_osapiwrappers_namedMounts
#include <supp/exportPull.h>
