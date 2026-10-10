# OpenSSL 3 libcrypto (without SHA, which is crypto/sha)
include(../openssl.cmake)

set(sources)
foreach(file asn1_dsa bsearch context core_algorithm core_fetch core_namemap cpt_err cversion der_writer ebcdic ex_data
             info init initthread mem mem_sec o_dir o_fopen o_init o_str o_time packet param_build param_build_set params
             params_dup params_from_text passphrase provider provider_child provider_conf provider_core
             provider_predefined punycode self_test_core sparse_array trace uid dso/dso_openssl dso/dso_lib dso/dso_err
             dso/dso_dl poly1305/poly1305)
  list(APPEND sources ${OPENSSL_DIR}/crypto/${file}.c)
endforeach()
set(ec_int128 ecp_nistp224.c ecp_nistp256.c ecp_nistp521.c)
openssl_collect_c(sources crypto/aes aes_core.c aes_cbc.c)
foreach(dir aria asn1 async bf bio blake2 buffer cast cmac cmp cms comp conf crmf ct dh dsa ec/curve448
            ec/curve448/arch_32 ec/curve448/arch_64 encode_decode err ess evp ffc hmac http idea kdf lhash md4 md5 mdc2
            modes objects ocsp pem pkcs12 pkcs7 property rand rc2 rc5 ripemd rsa seed siphash sm2 sm3 sm4 srp stack
            store ts txt_db ui x509 x509v3)
  openssl_collect_c(sources crypto/${dir})
endforeach()
openssl_collect_c(sources crypto/bn bn_sparc.c)
openssl_collect_c(sources crypto/camellia camellia.c cmll_cbc.c)
openssl_collect_c(sources crypto/des ncbc_enc.c)
openssl_collect_c(sources crypto/ec ${ec_int128} ecp_nistz256_table.c)
openssl_collect_c(sources crypto/rc4 rc4_enc.c rc4_skey.c)
openssl_collect_c(sources crypto/whrlpool wp_block.c)

if(OPENSSL_ASM)
  foreach(dir aes bn camellia chacha ec md5 modes poly1305 rc4 whrlpool)
    openssl_collect_asm(sources crypto/${dir})
  endforeach()
else()
  foreach(file aes/aes_core aes/aes_cbc chacha/chacha_enc mem_clr whrlpool/wp_block camellia/camellia camellia/cmll_cbc
               rc4/rc4_enc rc4/rc4_skey)
    list(APPEND sources ${OPENSSL_DIR}/crypto/${file}.c)
  endforeach()
endif()

set(c_options ${OPENSSL_C_OPTIONS})
set(source_options)
if(DAGOR_PLATFORM STREQUAL "windows")
  list(APPEND sources ${OPENSSL_DIR}/crypto/threads_win.c ${OPENSSL_DIR}/crypto/async/arch/async_win.c)
else()
  if(DAGOR_PLATFORM MATCHES "^(iOS|android)$")
    list(APPEND sources ${OPENSSL_DIR}/crypto/async/arch/async_null.c)
  else()
    list(APPEND sources ${OPENSSL_DIR}/crypto/async/arch/async_posix.c)
  endif()
  list(APPEND sources ${OPENSSL_DIR}/crypto/threads_pthread.c)
  list(TRANSFORM ec_int128 PREPEND "${OPENSSL_DIR}/crypto/ec/")
  list(APPEND sources ${ec_int128})
endif()
if(DAGOR_CC STREQUAL "gcc")
  # false positive of gcc 13: "rsaz_exp_x2.c:496:16: error: iteration 19 invokes undefined behavior"
  list(APPEND c_options -Wno-aggressive-loop-optimizations -Wno-discarded-qualifiers)
  if(DAGOR_SANITIZE STREQUAL "thread")
    list(APPEND c_options -fno-sanitize=thread)
  endif()
elseif(DAGOR_CC MATCHES "^(clang|clang-cl)$")
  list(APPEND c_options -Wno-incompatible-pointer-types-discards-qualifiers)
  if(DAGOR_SANITIZE STREQUAL "undefined")
    list(APPEND c_options -fno-sanitize=undefined)
  endif()
endif()
if(DAGOR_ARCH STREQUAL "e2k")
  list(APPEND c_options -Wno-reduced-alignment)
  list(APPEND source_options ${OPENSSL_DIR}/crypto/async/arch/async_posix.c -Dmakecontext=makecontext_e2k)
endif()

dagor_add_library(
  SOURCES ${sources}
  PRIVATE_INCLUDES ${OPENSSL_INCLUDES}
  PRIVATE_DEFINES ${OPENSSL_C_DEFINES}
  C_OPTIONS ${c_options}
  SOURCE_OPTIONS ${source_options}
  DEPS 3rdPartyLibs/openssl-3.x/crypto/sha
  LICENSE_FILES ${OPENSSL_DIR}/LICENSE.txt
)
