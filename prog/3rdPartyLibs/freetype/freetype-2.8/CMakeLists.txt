# FreeType 2.8 (the modules of the engine's font rendering; no bzip2/gzip/lzw streams)
set(sources)
foreach(name
    afangles
    afblue
    afcjk
    afdummy
    afglobal
    afhints
    afindic
    aflatin
    afloader
    afmodule
    afpic
    afranges
    afshaper
    afwarp)
  list(APPEND sources src/autofit/${name}.c)
endforeach()
foreach(name
    basepic
    ftadvanc
    ftcalc
    ftdbgmem
    ftgloadr
    fthash
    ftobjs
    ftoutln
    ftpic
    ftrfork
    ftsnames
    ftstream
    fttrigon
    ftutil
    ftapi
    ftbbox
    ftbdf
    ftbitmap
    ftcid
    ftdebug
    ftfntfmt
    ftfstype
    ftgasp
    ftglyph
    ftgxval
    ftinit
    ftlcdfil
    ftmm
    ftotval
    ftpatent
    ftpfr
    ftstroke
    ftsynth
    ftsystem
    fttype1
    ftwinfnt)
  list(APPEND sources src/base/${name}.c)
endforeach()
foreach(name bdfdrivr bdflib)
  list(APPEND sources src/bdf/${name}.c)
endforeach()
foreach(name ftcbasic ftccache ftcglyph ftcimage ftcmanag ftccmap ftcmru ftcsbits)
  list(APPEND sources src/cache/${name}.c)
endforeach()
foreach(name
    cffcmap
    cffdrivr
    cffgload
    cffload
    cffobjs
    cffparse
    cffpic
    cf2arrst
    cf2blues
    cf2error
    cf2font
    cf2ft
    cf2hints
    cf2intrp
    cf2read
    cf2stack)
  list(APPEND sources src/cff/${name}.c)
endforeach()
foreach(name cidgload cidload cidobjs cidparse cidriver)
  list(APPEND sources src/cid/${name}.c)
endforeach()
foreach(name
    gxvbsln
    gxvcommn
    gxvfeat
    gxvjust
    gxvkern
    gxvlcar
    gxvmod
    gxvmort
    gxvmort0
    gxvmort1
    gxvmort2
    gxvmort4
    gxvmort5
    gxvmorx
    gxvmorx0
    gxvmorx1
    gxvmorx2
    gxvmorx4
    gxvmorx5
    gxvopbd
    gxvprop
    gxvtrak)
  list(APPEND sources src/gxvalid/${name}.c)
endforeach()
foreach(name otvbase otvcommn otvgdef otvgpos otvgsub otvjstf otvmath otvmod)
  list(APPEND sources src/otvalid/${name}.c)
endforeach()
foreach(name pcfdrivr pcfread pcfutil)
  list(APPEND sources src/pcf/${name}.c)
endforeach()
foreach(name pfrcmap pfrdrivr pfrgload pfrload pfrobjs pfrsbit)
  list(APPEND sources src/pfr/${name}.c)
endforeach()
foreach(name afmparse psauxmod psconv psobjs t1cmap t1decode)
  list(APPEND sources src/psaux/${name}.c)
endforeach()
foreach(name pshalgo pshglob pshmod pshpic pshrec)
  list(APPEND sources src/pshinter/${name}.c)
endforeach()
foreach(name psmodule pspic)
  list(APPEND sources src/psnames/${name}.c)
endforeach()
foreach(name ftraster ftrend1 rastpic)
  list(APPEND sources src/raster/${name}.c)
endforeach()
foreach(name pngshim sfdriver sfntpic sfobjs ttbdf ttcmap ttkern ttload ttmtx ttpost ttsbit)
  list(APPEND sources src/sfnt/${name}.c)
endforeach()
foreach(name ftgrays ftsmooth ftspic)
  list(APPEND sources src/smooth/${name}.c)
endforeach()
foreach(name ttdriver ttgload ttgxvar ttinterp ttobjs ttpic ttpload ttsubpix)
  list(APPEND sources src/truetype/${name}.c)
endforeach()
foreach(name t1afm t1driver t1gload t1load t1objs t1parse)
  list(APPEND sources src/type1/${name}.c)
endforeach()
foreach(name t42drivr t42objs t42parse)
  list(APPEND sources src/type42/${name}.c)
endforeach()
foreach(name winfnt)
  list(APPEND sources src/winfonts/${name}.c)
endforeach()
set(source_options)
if(DAGOR_PLATFORM STREQUAL "macOS")
  list(APPEND sources src/base/ftmac.c)
  list(APPEND source_options src/bdf/bdflib.c -Wno-deprecated-declarations)
endif()
set(options)
if(DAGOR_CC STREQUAL "msvc")
  list(APPEND options /wd4267) # conversion from 'size_t' to 'int', possible loss of data
elseif(NOT DAGOR_MSVC_LIKE)
  list(APPEND options -Wno-unused-parameter)
endif()

dagor_add_library(
  SOURCES ${sources}
  PRIVATE_INCLUDES include src
  PRIVATE_DEFINES FT2_BUILD_LIBRARY
  COMPILE_OPTIONS ${options}
  SOURCE_OPTIONS ${source_options}
)
