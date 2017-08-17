#!/usr/bin/env bash
#
# presync.sh
#
# usage: presync.sh <filename> <outfilestem>
#
# This script carries out the operations required prior to syncing
# RiffTrax audio tracks to movies:
# 1. convert movie file to .mkv
# 2. extract audio and convert to .wav for sync

OUTMKV=$2.mkv

cmd1="ffmpeg -i \"$1\" -c:v copy -c:a copy ${OUTMKV}"
echo ${cmd1}
eval ${cmd1}

cmd2="mkvextract tracks ${OUTMKV} 1:$2.ac3"
echo ${cmd2}
eval ${cmd2}

cmd3="ffmpeg -i $2.ac3 -ac 2 $2.wav"
echo ${cmd3}
eval ${cmd3}
