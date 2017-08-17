#!/usr/bin/env bash
#
# postsync.sh
#
# usage: postsync.sh <filestem> <movie title> <series/episode ID>
#
# This script carries out the operations required after syncing RiffTrax audio
# 1. Multiplex audio to movie
# 2. Remove audio tracks
# 3. Remove .mkv file

cmd1="ffmpeg -i $1.mkv -i $1.mp3 \
             -map 0:v:0 -map 1:a:0 \
             -c:v copy -c:a libfdk_aac \
             -metadata title=\"RiffTrax: $2\" -y \
             \"RiffTrax - $3 - $2.mp4\""
echo ${cmd1}
eval ${cmd1}

cmd2="rm $1.ac3; rm $1.wav"
echo ${cmd2}
eval ${cmd2}

cmd3="rm $1.mkv; rm $1.mp3"
echo ${cmd3}
eval ${cmd3}

cmd4="rm $1.aup"
echo ${cmd4}
eval ${cmd4}

