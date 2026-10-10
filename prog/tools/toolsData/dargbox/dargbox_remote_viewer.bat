rem you can set this .bat file to open dargbox images by windows.
rem need only fix addpath to dargbox on your PC
pushd D:\dagor2\tools\dargbox
call dargbox.cmd -config:debug/useAddonVromSrc:b=no %1 %2 %3
popd