#!/usr/bin/env python

# Installing requirements in Debian/Ubuntu:
# sudo apt-get install python-{matplotlib,progressbar}
# ln -s /PATH/TO/pymclevel /PATH/TO/THIS/SCRIPT


import sys
import os
import subprocess
import os.path as osp
import matplotlib.pyplot as plt
from progressbar import ProgressBar, Percentage, Bar, ETA
from datetime import datetime
import numpy
import time
import logging
logging.basicConfig(level=logging.DEBUG)
from pymclevel import mclevel

def openfile(filename):
    if sys.platform.startswith('darwin'):
        subprocess.call(('open', filename))
    elif os.name == 'nt':  # works for sys.platform 'win32' and 'cygwin'
        os.system("start %s" % filename)  # could be os.startfile() too
    else:  # Assume POSIX (Linux, BSD, etc)
        subprocess.call(('xdg-open', filename))


def ore_name(ore):
    return world.materials[ore].name.replace(' Ore', '')


# Progress bar style
widgets = [' ', Percentage(), ' ', Bar(marker='.'), ' ', ETA(), ' ']

## Magic numbers
#CHUNK_HEIGHT = 35
BLOCK_ID = {
     0: ["Air",      'blue'],
     1: ["Stone",    'gray'],
     7: ["Bedrock",  'black'],
    10: ["Lava",    'yellow'],
    11: ["Still Lava", 'red'],
    14: ["Gold",     'gold'],
    15: ["Iron",     'orange'],
    16: ["Coal",     'darkgray'],
    21: ["Lapis",    'blue'],
    56: ["Diamond",  'cyan'],
    73: ["Redstone", 'red'],
}

start = time.clock()

## Open world:
try:
    levelfile = osp.expanduser('~/.minecraft/saves/%s/level.dat' % ("".join(sys.argv[1:2]) or 'Brave'))
    world = mclevel.fromFile(levelfile, readonly=True)
    outfilename = osp.expanduser('~/minecraft-%s_%s.svg' % (osp.basename(osp.dirname(levelfile)), datetime.now()))
    CHUNK_HEIGHT = int("".join(sys.argv[2:3]) or 50 or world.Height-1) + 1
except:
    raise
    print "usage: "+sys.argv[0]+" path/to/level.dat out-graph.png"
    sys.exit(-1)

print "Reading %s" % levelfile

## Initialize
ore_list = BLOCK_ID.keys()  # range(256)
ore_sums = {}
for ore in ore_list:
    ore_sums[ore] = numpy.zeros(CHUNK_HEIGHT)
chunk_max = world.chunkCount
chunk_count = 0

## Iterate over all blocks:
print "Overworld contains %d chunks. Analyzing ores..." % chunk_max
pbar = ProgressBar(widgets=widgets, maxval=chunk_max).start()


for cx, cz in world.allChunks:
    chunk = world.getChunk(cx, cz)
    chunk_count += 1
    for ore in ore_list:
        ore_sums[ore] += (chunk.Blocks[:, :, :CHUNK_HEIGHT] == ore).sum(0).sum(0)
    pbar.update(chunk_count)

# finish progress
pbar.finish()

print "Totals per chunk:"
for ore in ore_list:
    ore_sums[ore] /= float(chunk_count)  # Normalize
    print " - %-20s\t%8.2f" % (ore_name(ore), ore_sums[ore].sum())

print "Elapsed: %.2f seconds" % (time.clock()-start)

## Create plot:
#print "Saving plot to '%s'" % outfilename
for ore in ore_list:
    plt.plot(ore_sums[ore], label=ore_name(ore), color=world.materials[ore].color/255.0)
plt.legend()
plt.xlabel('Layer')
plt.ylabel('Blocks per chunk')
plt.yscale('log')
plt.grid()
plt.show()
#plt.savefig(outfilename, dpi=120)
#openfile(outfilename)
