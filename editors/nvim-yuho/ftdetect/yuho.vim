" Yuho filetype detection
" Recognizes .yh files as Yuho statute files

au BufRead,BufNewFile *.yh setfiletype yuho
au BufRead,BufNewFile statute.yh setfiletype yuho
au BufRead,BufNewFile test_statute.yh setfiletype yuho
