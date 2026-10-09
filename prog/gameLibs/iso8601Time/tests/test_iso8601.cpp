// Copyright (C) Gaijin Games KFT.  All rights reserved.

#include <catch2/catch_get_random_seed.hpp>
#include <catch2/catch_test_macros.hpp>
#include <iso8601Time/iso8601Time.h>
#include <math/random/dag_random.h>

// a random offset in [0, max_value], reproducible with Catch2's --rng-seed
static int random_offset(int max_value)
{
  dagor_random::set_rnd_seed(int(Catch::getSeed()));
  // cannot reliably use rnd_int for numbers bigger than 65536
  return int(dagor_random::rnd_float(0, max_value));
}

TEST_CASE("parse_rfc3339_timestamps", "[iso8601]")
{
  // results are in milliseconds
  CHECK(iso8601_parse("1969-12-31T23:59:58Z") == 0LL);
  CHECK(iso8601_parse("1969-12-31T23:59:59Z") == 0LL);
  CHECK(iso8601_parse("1969-12-31T23:59:59.123Z") == 0LL);
  CHECK(iso8601_parse("1969-12-31T23:59:59.999Z") == 0LL);
  CHECK(iso8601_parse("1970-01-01T00:00:00Z") == 0LL);
  CHECK(iso8601_parse("1970-01-01T00:00:00.001Z") == 1LL);
  CHECK(iso8601_parse("1970-01-01T00:00:00.01Z") == 10LL);
  CHECK(iso8601_parse("1970-01-01T00:00:00.1Z") == 100LL);
  CHECK(iso8601_parse("1970-01-01T00:00:00.123Z") == 123LL);
  CHECK(iso8601_parse("1970-01-01T00:00:01Z") == 1000LL);
  CHECK(iso8601_parse("2023-07-19T10:02:12.42Z") == 1689760932420LL);
  CHECK(iso8601_parse("2038-01-19T03:14:07Z") == 0x7FFFFFFFLL * 1000LL);
  CHECK(iso8601_parse("2038-01-19T03:14:08Z") == 0x80000000LL * 1000LL);
  CHECK(iso8601_parse("2106-02-07T06:28:15Z") == 0xFFFFFFFFLL * 1000LL);
  CHECK(iso8601_parse("2106-02-07T06:28:16Z") == 0x100000000LL * 1000LL);
}

TEST_CASE("dogfeed_rfc3339_timestamps", "[iso8601]")
{
  char buf[64];
  const int step = 5430889; // an arbitrary adequately large prime number
  const int offset = random_offset(step - 1);
  for (long long t = -0x80000000LL * 1000LL - step + offset; t < 0x80000000LL * 1000LL; t += step)
  {
    const long long expected = t > 0 ? t : 0;
    iso8601_format(t, buf, 64);
    const long long parseResult = iso8601_parse(buf);
    INFO(buf);
    CHECK(parseResult == expected);
  }
}

TEST_CASE("parse_rfc3339_timestamps_with_tz", "[iso8601]")
{
  // RCF3339: For example, 18:50:00-04:00 is the same time as 22:50:00Z
  const long long targetTime = iso8601_parse("2023-07-19T10:02:12.421Z");
  CHECK(targetTime == iso8601_parse("2023-07-19T10:02:12.421+00"));
  CHECK(targetTime == iso8601_parse("2023-07-19T10:02:12.421+0000"));
  CHECK(targetTime == iso8601_parse("2023-07-19T10:02:12.421+00:00"));
  CHECK(targetTime == iso8601_parse("2023-07-19T11:02:12.421+01"));
  CHECK(targetTime == iso8601_parse("2023-07-19T11:02:12.421+0100"));
  CHECK(targetTime == iso8601_parse("2023-07-19T11:02:12.421+01:00"));
  CHECK(targetTime == iso8601_parse("2023-07-19T09:02:12.421-01"));
  CHECK(targetTime == iso8601_parse("2023-07-19T09:02:12.421-0100"));
  CHECK(targetTime == iso8601_parse("2023-07-19T09:02:12.421-01:00"));
  CHECK(targetTime == iso8601_parse("2023-07-18T22:02:12.421-12"));
  CHECK(targetTime == iso8601_parse("2023-07-18T21:32:12.421-1230"));
  CHECK(targetTime == iso8601_parse("2023-07-18T21:17:12.421-12:45"));
  CHECK(targetTime == iso8601_parse("2023-07-20T00:02:12.421+14"));
  CHECK(targetTime == iso8601_parse("2023-07-20T00:32:12.421+1430"));
  CHECK(targetTime == iso8601_parse("2023-07-20T00:47:12.421+14:45"));

  CHECK(iso8601_parse("1970-01-01T00:00:00+10:00") == -10 * 60 * 60 * 1000LL);
  CHECK(iso8601_parse("1970-01-01T00:00:00+05:00") == -5 * 60 * 60 * 1000LL);
  CHECK(iso8601_parse("1970-01-01T00:00:00+00:01") == -60 * 1000LL);
  CHECK(iso8601_parse("1970-01-01T00:00:00+00:00") == 0LL);
  CHECK(iso8601_parse("1970-01-01T00:00:00-00:00") == 0LL);
  CHECK(iso8601_parse("1970-01-01T00:00:00-00:01") == 60 * 1000LL);
  CHECK(iso8601_parse("1970-01-01T00:00:00-00:02") == 2 * 60 * 1000LL);
  CHECK(iso8601_parse("1970-01-01T00:00:00-01:00") == 60 * 60 * 1000LL);
}

TEST_CASE("parse_iso8601_timestamps", "[iso8601]")
{
  // Example formats taken from https://ru.wikipedia.org/wiki/ISO_8601
  // formats checked by previous tests skipped

  // YYYY-MM
  CHECK(iso8601_parse("2023-08-01T00:00:00Z") == iso8601_parse("2023-08"));
  // YYYYMMDD
  CHECK(iso8601_parse("2023-08-01T00:00:00Z") == iso8601_parse("20230801"));
  // YYYY-MM-DD
  CHECK(iso8601_parse("2023-08-01T00:00:00Z") == iso8601_parse("2023-08-01"));
  // YYYYMMDDThhmmss
  CHECK(iso8601_parse("2023-08-01T11:22:33Z") == iso8601_parse("20230801T112233"));
  // YYYY-MM-DDThh:mm:ss
  CHECK(iso8601_parse("2023-08-01T11:22:33Z") == iso8601_parse("2023-08-01T11:22:33"));
  // YYYYMMDDThhmmss±hh
  CHECK(iso8601_parse("2023-08-01T11:22:33Z") == iso8601_parse("20230801T152233+04"));
  // YYYYMMDDThhmmss±hhmm
  CHECK(iso8601_parse("2023-08-01T11:22:33Z") == iso8601_parse("20230801T154233+0420"));
  // YYYY-MM-DDThh:mm:ss[.SSS]
  CHECK(iso8601_parse("2023-08-01T11:22:33.123Z") == iso8601_parse("2023-08-01T11:22:33.123"));

  // time variations
  // hhmm
  CHECK(iso8601_parse("2023-08-01T11:22:00Z") == iso8601_parse("2023-08-01T1122"));
  // hh:mm
  CHECK(iso8601_parse("2023-08-01T11:22:00Z") == iso8601_parse("2023-08-01T11:22"));

  // unholy abominations
  // YYYYThh
  CHECK(iso8601_parse("2023-01-01T11:00:00Z") == iso8601_parse("2023T11"));
  // YYYYThhmmss,SSS (with a comma)
  CHECK(iso8601_parse("2023-01-01T11:22:33.444Z") == iso8601_parse("2023T11:22:33,444"));
  // YYYY-MMThh:mm
  CHECK(iso8601_parse("2023-02-01T11:54:00Z") == iso8601_parse("2023-02T11:54"));
  // YYYYThhmmss.SSSSSSSSSSS...+hh
  CHECK(iso8601_parse("2023-01-01T11:22:33.444Z") == iso8601_parse("2023T13:22:33.4442348763248724638734984375692878769876435+02"));
}


TEST_CASE("parse_leap_second_timestamps", "[iso8601]")
{
  CHECK(iso8601_parse("2023-08-01T23:59:59.999Z") == iso8601_parse("2023-08-01T23:59:60Z"));
  CHECK(iso8601_parse("2023-08-01T23:59:59.999Z") == iso8601_parse("2023-08-01T23:59:60.000Z"));
  CHECK(iso8601_parse("2023-08-01T23:59:59.999Z") == iso8601_parse("2023-08-01T23:59:60.001Z"));
  CHECK(iso8601_parse("2023-08-01T23:59:59.999Z") == iso8601_parse("2023-08-01T23:59:60.010Z"));
  CHECK(iso8601_parse("2023-08-01T23:59:59.999Z") == iso8601_parse("2023-08-01T23:59:60.100Z"));
  CHECK(iso8601_parse("2023-08-01T23:59:59.999Z") == iso8601_parse("2023-08-01T23:59:60.999Z"));
}


TEST_CASE("parse_invalid", "[iso8601]")
{
  // YYYYMM is not valid b/c it cannot be distinguished from hhmmss
  CHECK(iso8601_parse("202308") == 0);

  CHECK(iso8601_parse("") == 0);
  CHECK(iso8601_parse("test") == 0);
  CHECK(iso8601_parse("123") == 0);
  CHECK(iso8601_parse("2012'11") == 0);
  CHECK(iso8601_parse("20121515") == 0);
  CHECK(iso8601_parse("20121200") == 0);
  CHECK(iso8601_parse("20120015") == 0);
  CHECK(iso8601_parse("20110229") == 0);
  CHECK(iso8601_parse("20120229") != 0); // 2012 is a leap year
  CHECK(iso8601_parse("21000229") == 0); // 2100 is not
  CHECK(iso8601_parse("20120333") == 0);
  CHECK(iso8601_parse("2012-") == 0);
  CHECK(iso8601_parse("2012-03-") == 0);
  CHECK(iso8601_parse("2012-0303") == 0);
  CHECK(iso8601_parse("201203-03") == 0);
  CHECK(iso8601_parse("2012-T00") == 0);
  CHECK(iso8601_parse("201203-T00") == 0);
  CHECK(iso8601_parse("2012T00:") == 0);
  CHECK(iso8601_parse("2012T00:00:") == 0);
  CHECK(iso8601_parse("2012T00:Z") == 0);
  CHECK(iso8601_parse("2012T00:00:Z") == 0);
  CHECK(iso8601_parse("2012T00:00:.001") == 0);
  CHECK(iso8601_parse("2012T00:00:.001Z") == 0);
  CHECK(iso8601_parse("2012T00:0000") == 0);
  CHECK(iso8601_parse("2012T0000:00") == 0);
  CHECK(iso8601_parse("20120305T00:00:99") == 0);
  CHECK(iso8601_parse("20120305T00-00-00") == 0);
  CHECK(iso8601_parse("20120305X000000") == 0);
  CHECK(iso8601_parse("20120305T00000") == 0);
  CHECK(iso8601_parse("20120305T000") == 0);
  CHECK(iso8601_parse("20120305T0") == 0);
  CHECK(iso8601_parse("20120305T010203.") == 0);
  CHECK(iso8601_parse("20120305T010203.Z") == 0);
  CHECK(iso8601_parse("20120305T010203.+0001") == 0);
  CHECK(iso8601_parse("20120305T010203.a") == 0);
  CHECK(iso8601_parse("20120305T010203!123Z") == 0);
  CHECK(iso8601_parse("20120305T0a0203.123Z") == 0);
  CHECK(iso8601_parse("20120305T010203.123+99") == 0);
  CHECK(iso8601_parse("20120305T010203.123+15") == 0); // 14 is maximum hour offset
  CHECK(iso8601_parse("20120305T010203.123-99") == 0);
  CHECK(iso8601_parse("20120305T010203.123-15") == 0);
  CHECK(iso8601_parse("2012asdasd") == 0);
  CHECK(iso8601_parse("201201asdasd") == 0);
  CHECK(iso8601_parse("20120101asdasd") == 0);
  CHECK(iso8601_parse("20120101Tasdasd") == 0);
  CHECK(iso8601_parse("20120101T00asdasd") == 0);
  CHECK(iso8601_parse("20120101T0000asdasd") == 0);
  CHECK(iso8601_parse("20120101T000000asdasd") == 0);
  CHECK(iso8601_parse("20120101T000000.001asdasd") == 0);
  CHECK(iso8601_parse("20120101T000000Zasdasd") == 0);
  CHECK(iso8601_parse("20120101T000000+00asdasd") == 0);
  CHECK(iso8601_parse("20120101T000000+0000asdasd") == 0);
}
