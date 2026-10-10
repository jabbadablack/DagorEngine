# Every archive the build downloads: official vendor URLs pinned by SHA256 (tools.hostGuard checks that each entry has
# one and that none points at Gaijin hosts). Bumping a version means changing its URLs and hashes here together.
# See dagor_sdk() in prog/cmake/DagorFetch.cmake for the format.

# LLVM: only the tools the build runs are unpacked (the archives also hold LLVM's own development libraries)
set(_llvm https://github.com/llvm/llvm-project/releases/download/llvmorg-21.1.8)
set(_llvm_win_tools clang clang-cl lld-link llvm-lib llvm-ar llvm-rc llvm-mt llvm-profdata llvm-cov llvm-symbolizer
  clang-format clang-tidy clang-scan-deps)
list(TRANSFORM _llvm_win_tools PREPEND "*/bin/")
list(TRANSFORM _llvm_win_tools APPEND ".exe")
set(_llvm_win ${_llvm_win_tools} */bin/libclang.dll */lib/clang/* */LICENSE.TXT)
set(_llvm_unix_tools clang clang-21 clang++ clang-cl lld ld.lld lld-link llvm-ar llvm-ranlib llvm-lib llvm-profdata
  llvm-cov llvm-symbolizer clang-format clang-tidy clang-scan-deps)
list(TRANSFORM _llvm_unix_tools PREPEND "*/bin/")
set(_llvm_unix ${_llvm_unix_tools} */lib/libclang.* */lib/libclang-cpp.* */lib/clang/* */LICENSE.TXT)
dagor_sdk(llvm 21.1.8
  windows-x86_64
    URL ${_llvm}/clang+llvm-21.1.8-x86_64-pc-windows-msvc.tar.xz
    SHA256 749d22f565fcd5718dbed06512572d0e5353b502c03fe1f7f17ee8b8aca21a47
    EXTRACT ${_llvm_win}
  windows-arm64
    URL ${_llvm}/clang+llvm-21.1.8-aarch64-pc-windows-msvc.tar.xz
    SHA256 f214b1226d8de005b5f691dd29d9dfea2b49e22d0de445429916173dbb626f7f
    EXTRACT ${_llvm_win}
  linux-x86_64
    URL ${_llvm}/LLVM-21.1.8-Linux-X64.tar.xz
    SHA256 b3b7f2801d15d50736acea3c73982994d025b01c2f035b91ae3b49d1b575732b
    EXTRACT ${_llvm_unix}
  linux-arm64
    URL ${_llvm}/LLVM-21.1.8-Linux-ARM64.tar.xz
    SHA256 65ce0b329514e5643407db2d02a5bd34bf33d159055dafa82825c8385bd01993
    EXTRACT ${_llvm_unix}
  macOS-arm64
    URL ${_llvm}/LLVM-21.1.8-macOS-ARM64.tar.xz
    SHA256 b95bdd32a33a81ee4d40363aaeb26728a26783fcef26a4d80f65457433ea4669
    EXTRACT ${_llvm_unix}
)
unset(_llvm)
unset(_llvm_win)
unset(_llvm_win_tools)
unset(_llvm_unix)
unset(_llvm_unix_tools)

# Linux uses the distro's nasm
dagor_sdk(nasm 2.16
  windows-x86_64
    URL https://www.nasm.us/pub/nasm/releasebuilds/2.16/win64/nasm-2.16-win64.zip
    SHA256 b50871c27e2db1492bd2464871992c3c09b54d171264e4cda3e32342ab3df785
  windows-arm64
    URL https://www.nasm.us/pub/nasm/releasebuilds/2.16/win64/nasm-2.16-win64.zip
    SHA256 b50871c27e2db1492bd2464871992c3c09b54d171264e4cda3e32342ab3df785
  macOS-x86_64
    URL https://www.nasm.us/pub/nasm/releasebuilds/2.16/macosx/nasm-2.16-macosx.zip
    SHA256 fa0aca18ac11baefa9090f22fe372903a36beecf73dc998f2fdb90632eec2b1e
  macOS-arm64
    URL https://www.nasm.us/pub/nasm/releasebuilds/2.16/macosx/nasm-2.16-macosx.zip
    SHA256 fa0aca18ac11baefa9090f22fe372903a36beecf73dc998f2fdb90632eec2b1e
)

# NVIDIA NVAPI R610 (pinned to the commit of the release: the repository's main branch moves on)
dagor_sdk(nvapi R610
  any
    URL https://github.com/NVIDIA/nvapi/archive/cd6918f60b3c9a0476fdfe7e89bb32330602049d.zip
    SHA256 e9832432139331aef90356c78f92a0ad7d238fc527128ad9f51350614d3c598a
    FILE nvapi-R610.zip
    EXTRACT */*.h */amd64/* */x86/* */License.txt
)

# Microsoft DirectX 12 Agility SDK (headers, d3dx12 and the redistributable D3D12Core/SDKLayers)
dagor_sdk(agility 1.619.3
  any
    URL https://www.nuget.org/api/v2/package/Microsoft.Direct3D.D3D12/1.619.3
    SHA256 43a7d5a3973812eb4b42623fae5275c790a005b8e48b8d7f5bb43cef39e073c5
    FILE Microsoft.Direct3D.D3D12.1.619.3.zip
    EXTRACT build/native/* LICENSE.txt LICENSE-CODE.txt
)
