#!/bin/sh
set -eu
cd "$(dirname "$0")"
FFMPEG=${FFMPEG:-ffmpeg}
"$FFMPEG" -hide_banner -y -loglevel warning \
-loop 1 -framerate 24 -t 10 -i cena-01.png \
-loop 1 -framerate 24 -t 14.625 -i cena-02.png \
-loop 1 -framerate 24 -t 13 -i cena-03.png \
-loop 1 -framerate 24 -t 14.0833 -i cena-04.png \
-loop 1 -framerate 24 -t 14.292 -i cena-05.png \
-loop 1 -framerate 24 -t 10 -i cena-06.png \
-loop 1 -framerate 24 -t 14 -i cena-07.png \
-i narracao-01.mp3 -i narracao-02.mp3 -i narracao-03.mp3 \
-filter_complex '[0:v]scale=960:540,setsar=1[v0];[1:v]scale=960:540,setsar=1[v1];[2:v]scale=960:540,setsar=1[v2];[3:v]scale=960:540,setsar=1[v3];[4:v]scale=960:540,setsar=1[v4];[5:v]scale=960:540,setsar=1[v5];[6:v]scale=960:540,setsar=1[v6];[v0][v1][v2][v3][v4][v5][v6]concat=n=7:v=1:a=0,trim=duration=90,fade=t=out:st=89:d=1[v];[7:a][8:a][9:a]concat=n=3:v=0:a=1,apad,atrim=duration=90[a]' \
-map '[v]' -map '[a]' -t 90 -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart primeiro-computador-estilo-03.mp4
