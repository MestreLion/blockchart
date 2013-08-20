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
import pprint
from datetime import datetime
from xdg.BaseDirectory import xdg_cache_home

workdir = osp.join(xdg_cache_home, 'minecraft')
if not osp.exists(workdir):
    os.makedirs(workdir)


def launchfile(filename):
    if sys.platform.startswith('darwin'):
        subprocess.call(('open', filename))
    elif os.name == 'nt':  # works for sys.platform 'win32' and 'cygwin'
        os.system("start %s" % filename)  # could be os.startfile() too
    else:  # Assume POSIX (Linux, BSD, etc)
        subprocess.call(('xdg-open', filename))


def main(args):
    from pymclevel import mclevel

    def openworld(name):
        if osp.isfile(name):
            return mclevel.fromFile(name, readonly=True)
        else:
            return mclevel.loadWorld(name)

    def ore_name(ore):
        return "%3d %s" % (ore, world.materials[ore].name.replace(' Ore', ''))

    def ore_color(ore):
        if ore in ores:
            return ores[ore]['color']
        else:
            return world.materials[ore].color/255.0

    def readworld(world):
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
        log.info("Saving block data to cache file '%s'", datacache)
        data = dict(LevelName=world.LevelName,
                    filename=world.filename,
                    LastPlayed=world.LastPlayed,
                    chunk_count=chunk_count,
                    dist=dist.tolist(),)
        with open(datacache, 'w') as f:
            json.dump(data, f, indent=0, separators=(',', ':'))
        return chunk_count, dist

    world = openworld(args.world)
    datacache = osp.join(workdir, "%s_%s.json" %
                         (myname, hashlib.md5(world.filename).hexdigest()))
    maxy = args.maxy + 1
    MAXHEIGHT = world.Height
    MAXBLOCKS = 256

    ores = {
         0: dict(color='blue'),      # Air
         1: dict(color='gray'),      # Stone
         7: dict(color='black'),     # Bedrock
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


    if osp.isfile(datacache):
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
    else:
        chunk_count, dist = readworld(world)

    # Merge blocks like Still/Active Lava, Glowing/Normal Redstone Ore, etc
    for i, j in [[8, 9], [10, 11], [74, 73]]:  # also perhaps [75, 76], [93, 94], [123, 124] [149, 150]
        dist[j] += dist[i]
        dist[i] -= dist[i]

    # small "hack" for tall grass name
    world.materials[(31,0)].name = world.materials[(31,1)].name

    # Normalize per chunk
    sums = numpy.zeros(MAXBLOCKS)
    ore_norm = dist / float(chunk_count)
    log.info("Total per chunk and Grand Total:")
    for ore in xrange(MAXBLOCKS):
        sums[ore] = dist[ore, :maxy].sum()
        if sums[ore] > 0:
            log.info("%-20s\t%8.2f\t%9d", ore_name(ore),
                                          sums[ore] / float(chunk_count),
                                          sums[ore])

    sums_norm = sums / float(chunk_count)


    ## Create plot:
    #outfile = osp.join(workdir, '%s-%s_%s.svg' % (myname, world.LevelName, datetime.now()))
    #print "Saving plot to '%s'" % outfile
    for ore in xrange(MAXBLOCKS):
        if ore in includes or sums[ore] > 0 and ore not in excludes:
            plt.plot(ore_norm[ore, :maxy], label=ore_name(ore),
                     color=ore_color(ore), linewidth=2 if ore in ores else 1)
    plt.legend()
    plt.xlabel('Layer')
    plt.ylabel('Blocks per chunk')
    if args.semilog:
        plt.semilogy()
    plt.grid()
    plt.show()
    #plt.savefig(outfile, dpi=120)
    #openfile(outfile)


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

    parser.add_argument('--maxy', '-y', dest='maxy',
                        default=70,
                        type=int,
                        help="Y (layer/height) upper bound. This only affects plotting,"
                        " as the world's full height will be read for caching purposes."
                        "  [default: 70]")

    parser.add_argument(dest='world',
                        default="Brave", nargs="?",  # @@
                        help="Minecraft world, either its 'level.dat' file"
                        " or a name under '~/.minecraft/saves' folder")

    return parser.parse_args(args)


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
