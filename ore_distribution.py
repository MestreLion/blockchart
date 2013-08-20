#!/usr/bin/env python

# Installing requirements in Debian/Ubuntu:
# sudo apt-get install python-{matplotlib,progressbar}
# ln -s /PATH/TO/pymclevel /PATH/TO/THIS/SCRIPT

# http://nemesis.evalq.net/RedPower2/ore_dist/

import sys
import os
import subprocess
import os.path as osp
import matplotlib.pyplot as plt
import progressbar
import argparse
import numpy
import time
import logging
import json
import hashlib
import re
from datetime import datetime
from xdg.BaseDirectory import xdg_cache_home

from template import template


def launchfile(filename):
    if sys.platform.startswith('darwin'):
        subprocess.call(('open', filename))
    elif os.name == 'nt':  # works for sys.platform 'win32' and 'cygwin'
        os.system("start %s" % filename)  # could be os.startfile() too
    else:  # Assume POSIX (Linux, BSD, etc)
        subprocess.call(('xdg-open', filename))

def cachefile(filename):
    return osp.join(workdir, "%s_%s" % (myname, filename))

def main(args):
    from pymclevel import mclevel

    def openworld(name):
        if osp.isfile(name):
            return mclevel.fromFile(name, readonly=True)
        else:
            return mclevel.loadWorld(name)

    def ore_name(ore):
        return "%3d %s" % (ore, re.sub(' \(.+\)$', '',
                                       world.materials[ore].name.replace(' Ore', '')))

    def ore_color(ore):
        if ore in ores:
            return ores[ore]['color']
        else:
            return world.materials[ore].color/255.0

    def readworld(world):
        # extract data
        log.info("Extracting '%s' block data from '%s'",
                 world.LevelName, world.filename)
        start = time.clock()
        chunk_count = world.chunkCount
        pbar = progressbar.ProgressBar(widgets=[' ', progressbar.Percentage(),
                                                ' Chunk ', progressbar.SimpleProgress(),
                                                ' ', progressbar.Bar('.'),
                                                ' ', progressbar.ETA(), ' '],
                                       maxval=chunk_count).start()
        dist = numpy.zeros((MAXBLOCKS, MAXHEIGHT))
        for cx, cz in world.allChunks:
            chunk = world.getChunk(cx, cz)
            for y in xrange(MAXHEIGHT):
                dist[:, y] += numpy.bincount(chunk.Blocks[:, :, y].ravel(),
                                             minlength=MAXBLOCKS)
            pbar.update(pbar.currval+1)
        pbar.finish()
        log.info("Data from %d chunks extracted in %.2f seconds",
                 chunk_count, time.clock()-start)

        # save data
        log.info("Saving block data to cache file '%s'", datacache)
        data = dict(LevelName=world.LevelName,
                    filename=world.filename,
                    LastPlayed=world.LastPlayed,
                    chunk_count=chunk_count,
                    dist=dist.tolist(),)
        with open(datacache, 'w') as f:
            json.dump(data, f, indent=0, separators=(',', ':'))

        return chunk_count, dist

    # open world and set constants
    world = openworld(args.world)
    datacache = cachefile("%s.json" % hashlib.md5(world.filename).hexdigest())
    htmlchart = cachefile("%s.html" % world.LevelName)
    imgchart  = cachefile("%s_%s.svg" % (world.LevelName, datetime.now()))

    maxy = args.maxy + 1
    MAXHEIGHT = world.Height  # world max y-layer + 1
    MAXBLOCKS = 256           # world max block ID + 1

    ores = {
#         0: dict(color='blue'),      # Air
#         1: dict(color='gray'),      # Stone
#         7: dict(color='black'),     # Bedrock
        10: dict(color='yellow'),    # Lava
        14: dict(color='gold'),      # Gold
        15: dict(color='orange'),    # Iron
        16: dict(color='darkgray'),  # Coal
        21: dict(color='blue'),      # Lapis
        56: dict(color='cyan'),      # Diamond
        73: dict(color='red'),       # Redstone
       129: dict(color='green')      # Emerald
    }

    includes = []
    excludes = []

    if args.rebuild_cache or not osp.isfile(datacache):
        chunk_count, dist = readworld(world)
    else:
        log.info("Reading '%s' data from cache '%s'", world.LevelName, datacache)
        try:
            with open(datacache, 'r') as f:
                data = json.load(f)
            if data['LastPlayed'] == world.LastPlayed:
                chunk_count = data['chunk_count']
                dist = numpy.asarray(data['dist'])
            else:
                log.warn("Cache is outdated, discarding.")
                chunk_count, dist = readworld(world)
        except Exception:
            chunk_count, dist = readworld(world)

    # Merge blocks like Still/Active Lava, Glowing/Normal Redstone Ore, etc
    for i, j in [[8, 9], [10, 11], [74, 73]]:  # also perhaps [75, 76], [93, 94], [123, 124] [149, 150]
        dist[j] += dist[i]
        dist[i] -= dist[i]

    # small "hack" for tall grass name
    world.materials[(31,0)].name = world.materials[(31,1)].name

    # Normalize per chunk
    dist_norm = dist / float(chunk_count)

    # calculate all derived data
    htmldata = {}
    sums = numpy.zeros(MAXBLOCKS)
    sums_norm = numpy.zeros(MAXBLOCKS)
    log.info("Total per chunk and Grand Total out of %d chunks:" % chunk_count)
    for ore in xrange(MAXBLOCKS):
        sums[ore] = dist[ore, :maxy].sum()
        sums_norm[ore] = dist_norm[ore, :maxy].sum()
        if sums[ore] > 0:
            htmldata[ore] = dict(active=ore in ores,
                                 sum=sums_norm[ore],
                                 label=ore_name(ore),
                                 data=zip(xrange(maxy), dist_norm[ore])
                                 )
            log.info("%-20s\t%8.2f\t%9d", ore_name(ore),
                                          sums_norm[ore],
                                          sums[ore])

    # create and open html chart
    with open(htmlchart, 'w') as f:
        htmltemp = template.replace('var chunks = 0;',
                                    'var chunks = %d;' % chunk_count)
        htmltemp = htmltemp.replace('var datasets = {};',
                                    'var datasets = %s;' % json.dumps(htmldata))
        f.write(htmltemp)
    launchfile(htmlchart)

    # create and open img plot
    for ore in xrange(MAXBLOCKS):
        if ore in includes or sums[ore] > 0 and ore not in excludes:
            plt.plot(dist_norm[ore, :maxy], label=ore_name(ore),
                     color=ore_color(ore), linewidth=2 if ore in ores else 1)
    plt.legend()
    plt.xlabel('Layer')
    plt.ylabel('Blocks per chunk')
    if args.semilog:
        plt.semilogy()
    plt.grid()
    #plt.show()
    #plt.savefig(imgchart, dpi=120)
    #launchfile(imgchart)


def setuplogging(level='INFO'):
    log = logging.getLogger()
    log.setLevel(level)
    sh = logging.StreamHandler()
    sh.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    #sh.setLevel(level)
    log.addHandler(sh)
    try:
        fh = logging.FileHandler(osp.join(workdir, "%s.log" % myname))
        fh.setFormatter(logging.Formatter('%(asctime)s\t%(levelname)s\t%(message)s'))
        log.addHandler(fh)
    except IOError as e:  # Probably access denied
        log.warn("%s\nLogging will not work.", e)
    return log


def parseargs(args=None):
    parser = argparse.ArgumentParser(
        description="Plot ore distribution of Minecraft worlds.",)

    loglevels = ['debug', 'info', 'warn', 'error', 'critical']
    logdefault = 'info'
    parser.add_argument('--loglevel', '-l', dest='loglevel',
                        default=logdefault, choices=loglevels,
                        help="set verbosity level. [default: '%s']" % logdefault)

    parser.add_argument('--semilog', '-s', dest='semilog',
                        default=False,
                        action='store_true',
                        help='plots a semi-log graph instead of a linear one.')

    parser.add_argument('--rebuild-cache', '-c', dest='rebuild_cache',
                        default=False,
                        action='store_false',
                        help='force rebuild of block data cache.')

    parser.add_argument('--maxy', '-y', dest='maxy',
                        default=130,
                        type=int,
                        help="Y (layer/height) upper bound. This only affects plotting,"
                        " as the world's full height will be read for caching purposes."
                        "  [default: 130]")

    #TODO: add all of --{min,max}{y,x,z}

    parser.add_argument(dest='world',
                        default="Brave", nargs="?",  # @@
                        help="Minecraft world, either its 'level.dat' file"
                        " or a name under '~/.minecraft/saves' folder")

    return parser.parse_args(args)


workdir = osp.join(xdg_cache_home, 'minecraft')
if not osp.exists(workdir):
    os.makedirs(workdir)

if __name__ != '__main__':
    myname = __name__
    log = logging.getLogger(myname)
    log.addHandler(logging.NullHandler())

else:
    myname = osp.basename(osp.splitext(__file__)[0])
    args = parseargs()
    log = setuplogging(args.loglevel.upper())
    try:
        sys.exit(main(args))
    except Exception as e:
        log.critical(e, exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
        pass
