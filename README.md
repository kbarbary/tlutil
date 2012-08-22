tlutil
======

Utilities for dealing with timelapses.

Requirements 
------------
* Python 2.6 or greater (for argparse module)
* Python Imaging Library (PIL)

Description
-----------
Currently, this package provides one python script, `tl-download`:

```
usage: tl-download [-h] [-d] INDIR [OUTDIR]

Detect timelapse image sequences based on timestamps and move timelapses to
new directory.

positional arguments:
  INDIR          Directory in which to look for images
  OUTDIR         Move timelapses to given timelapse directory.

optional arguments:
  -h, --help     show this help message and exit
  -d, --dry-run  Show results of image parsing, but do not move any images.
```