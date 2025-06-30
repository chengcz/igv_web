#!/usr/bin/env python

import os
import sys
import time
import argparse
from os import listdir
from gzip import open as gopen
from os.path import join as pathjoin
from os.path import isdir, isfile, islink, abspath, realpath, exists, basename, dirname

user = os.getenv("USER")
if not user:
    user = "igv_anonymous"

IGVURL = "http://${SERVERIP}:${PORT}/"

ThisScriptPath = dirname(abspath(__file__))
RESOURCEDIR = pathjoin(ThisScriptPath, "igv-webapp/resources/data/", user)
RESOURCEURL = pathjoin("resources/data/", user)


def _bamWalkMan(dirs, depth=3):
    Cache = []
    skipping = ("data_deliver", "?", "java", "log", "benchmark", "monitor", "summary")
    filelst = [
        pathjoin(dirs, x) for x in listdir(dirs)
        if (x not in skipping) and not x.startswith('.')
    ]
    for x in filelst:
        if islink(x):
            x = realpath(x)

        if not exists(x):
            continue

        if isfile(x):
            if x.endswith(".bam"):
                Cache.append(x)

        elif isdir(x) and (depth > 0):
            Cache.extend(_bamWalkMan(x, depth=depth-1))

        elif isdir(x):
            pass

        else:
            print(" >>> illegal file type: {}".format(x))

    return Cache


def linkProjectDirToResources(dirs, genome="hg19"):
    bamlst = _bamWalkMan(dirs)
    # bamlst = set([abspath(x) for x in bamlst])

    temp = [x for x in bamlst if x.endswith("_sorted_dedup.bam")]
    if not temp:
        temp = [x for x in bamlst if x.endswith("_sorted.bam")]

    if temp:
        bamlst = temp

    cache = {}
    for bam in bamlst:
        name = basename(bam).split("sorted")[0].strip("_")
        cache.setdefault(name, []).append(bam)

    IgvFileLst = []
    projectid = dirname(bam).split('/')[-2][:30]
    for x, y in cache.items():
        IgvFileLst.append(linkBamToResources(y[0], projectid))
    return IgvFileLst


def linkBamToResources(bam, subfolder=None):
    targetDir, targetUrl = _check_subfolder(subfolder)

    targetName = basename(bam)
    # bam = abspath(bam)
    if exists("{}.bai".format(bam)):
        index = "{}.bai".format(bam)
    elif exists("{}.bai".format(bam.rpartition(".")[0])):
        index = "{}.bai".format(bam.rpartition(".")[0])
    else:
        print("bam index file not found, skipping")
        return

    targetBam = pathjoin(targetDir, targetName)
    _create_file_link(bam, targetBam)

    targetIndex = pathjoin(targetDir, '{}.bai'.format(targetName))
    _create_file_link(index, targetIndex)

    return pathjoin(targetUrl, targetName)


def _check_subfolder(subfolder=None):
    if not isinstance(subfolder, str):
        subfolder = "igv_" + time.strftime("%Y%m%d", time.localtime())
    if "/" in subfolder:
        subfolder = subfolder.replace("/", "_")

    targetDir = pathjoin(RESOURCEDIR, subfolder)
    targetUrl = pathjoin(RESOURCEURL, subfolder)
    if not exists(targetDir):
        os.makedirs(targetDir, mode=0o775)
    return targetDir, targetUrl


def _create_file_link(src, dst):
    if exists(dst):
        os.unlink(dst)
    os.symlink(src, dst)


def linkBedToResources(BedFile, subfolder=None):
    targetDir, targetUrl = _check_subfolder(subfolder)

    targetName = basename(BedFile)
    # BedFile = abspath(BedFile)
    targetBed = pathjoin(targetDir, targetName)
    _create_file_link(BedFile, targetBed)

    return pathjoin(targetUrl, targetName)


def linkFastaToResources(FastaFile, subfolder=None):
    targetDir, targetUrl = _check_subfolder(subfolder)

    IndexFile = "{}.fai".format(FastaFile)
    assert exists(IndexFile)

    targetName = basename(FastaFile)
    targetFile = pathjoin(targetDir, targetName)
    _create_file_link(FastaFile, targetFile)

    targetIndex = pathjoin(targetDir, '{}.fai'.format(targetName))
    _create_file_link(IndexFile, targetIndex)

    print("------------------------------")
    print(">>> IGV server Genome URL")
    print("    genome url: {}".format(pathjoin(targetUrl, targetName)))
    print("    index url:  {}".format(pathjoin(targetUrl, '{}.fai'.format(targetName))))
    print("------------------------------")
    return None


def print_IGVurl(BamIgv, genome="hg19", vcfFile=None, flagAllUrl=False):

    assert isinstance(BamIgv, str)
    if not all(map(lambda x: x.startswith("resources/data"), BamIgv.split(","))):
        return
    assert genome in ("hg19", "mm10", "hg38")

    print("")
    if (not vcfFile) or (not exists(vcfFile)):
        name = ','.join([basename(x).split("sorted")[0].strip("_") for x in BamIgv.split(",")])
        print(">>> {}".format(name))
        print("    {}?file={}&genome={}".format(IGVURL, BamIgv, genome))
        print("------------------------------")
        return

    locus = {}
    fopen, fmode = (gopen, "rt") if vcfFile.endswith(".gz") else (open, "r")
    with fopen(vcfFile, fmode) as fi:
        for line in fi:
            if line.startswith("#"):
                continue
            chrom, pos, _, ref, alt = line.strip().split("\t")[:5]
            locus.setdefault((chrom, pos), []).append((chrom, pos, ref, alt))

    for idx, ((chrom, pos), varlst) in enumerate(locus.items()):
        if (flagAllUrl is False) and (idx >= 10):
            print("    ... too many locus, skipping ...")
            break
        varlst = " || ".join([":".join(x) for x in varlst])
        url = "{}?file={}&genome={}&locus={}:{}".format(IGVURL, BamIgv, genome, chrom, pos)
        print("    {: <3}: {}".format(idx+1, varlst))
        print("         {}".format(url))
        print("------------------------------")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("BamFile", nargs="*", help="Bam/Bed file or Project Dir")
    parser.add_argument(
        "-g", "--genome",
        choices=("hg19", "mm10", "hg38"),
        default="hg19",
        help="genome version, default: hg19"
    )
    parser.add_argument(
        "-v", "--vcf",
        help="vcf file for site IGV url"
    )
    parser.add_argument(
        "-a", "--all-url",
        dest="flagAllUrl",
        action="store_true",
        help="generate url of all variants in vcf file"
    )
    parser.add_argument(
        "-m", "--merge",
        dest="flagOneUrl",
        action="store_true",
        help="generate single url for multiple bam files"
    )
    args = parser.parse_args()

    if len(sys.argv) < 2:
        parser.print_help()
        exit(0)

    # TarOpts = sys.argv[1:]
    TarOpts = args.BamFile

    if len(TarOpts) == 0:
        print("="*40)
        print(" input positional params is Null, exit.")
        print("="*40)
        exit(0)

    print()
    print("\033[31m >>> IGV web URL: <<< \n    {}\033[0m".format(IGVURL))

    print("="*40)
    print(" >>>>> Starting <<<<< ")
    print(" target Dir: {} ".format(RESOURCEDIR))
    print("="*40)
    print()

    IgvFileLst = []
    for TarOpt in TarOpts:
        TarOpt = abspath(TarOpt)

        if isdir(TarOpt):
            IgvFileLst.extend(linkProjectDirToResources(TarOpt, genome=args.genome))
        elif isfile(TarOpt) and TarOpt.endswith("bam"):
            IgvFileLst.append(linkBamToResources(TarOpt))
        elif isfile(TarOpt) and TarOpt.endswith("bed"):
            IgvFileLst.append(linkBedToResources(TarOpt))
        elif isfile(TarOpt) and TarOpt.endswith(("fa", "fasta", "fa.gz", "fasta.gz")):
            IgvFileLst.append(linkFastaToResources(TarOpt))
        else:
            print(" >>> Illegal input option: {} <<< ".format(TarOpt))
            print()

    IgvFileLst = [x for x in IgvFileLst if x]
    if len(IgvFileLst) == 0:
        print("="*40)
        print(" input valid bam file(BamFile/ProjectDir) is Null, exit.")
        print("="*40)
        exit(0)

    if args.flagOneUrl:
        print_IGVurl(",".join(IgvFileLst), args.genome, args.vcf, args.flagAllUrl)
        exit(0)

    for igvfile in IgvFileLst:
        print_IGVurl(igvfile, args.genome, args.vcf, args.flagAllUrl)

    print()
    print("="*40)
    print(" >>>>> END <<<<< ")
    print("="*40)
