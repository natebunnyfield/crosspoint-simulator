#!/bin/bash
# usage: arm.sh <name>   (installs nothing; runs the installed app)
SP=${SP:?set SP to a scratch dir holding pin.sh}
D=B0E25998-5905-45F9-A491-C81C1F269684
N=$1; ZEN=${ZEN:-1}
cd $SP; bash $SP/pin.sh >/dev/null
rm -f $N.mov
xcrun simctl io $D recordVideo --codec h264 --force $N.mov > $N.rec.log 2>&1 &
REC=$!
sleep 1
SIMCTL_CHILD_CROSSPOINT_SIM_ZEN=$ZEN SIMCTL_CHILD_CROSSPOINT_SIM_LOG_PRESENTS=1 SIMCTL_CHILD_CROSSPOINT_SIM_INPUT_SCRIPT='4000:QTAP:RIGHT;5000:QTAP:RIGHT;6000:QTAP:RIGHT;9000:QTAP:DOWN:80;12000:QTAP:UP:80;15000:QTAP:DOWN:80;18000:QTAP:UP:80;21000:QTAP:DOWN:80;24000:QTAP:UP:80' xcrun simctl launch --console-pty --terminate-running-process $D com.natebunnyfield.crosspoint.x3 > $SP/$N.log 2>&1 &
L=$!
sleep 28
kill -INT $REC; sleep 2
kill $L 2>/dev/null; pkill -f "simctl launch --console-pty"
xcrun simctl terminate $D com.natebunnyfield.crosspoint.x3 2>/dev/null
echo "activity: $(grep -c 'Entering activity: EpubReader' $N.log) reader entries"
echo "font steps (Capture lines): $(grep -c 'Capture: page' $N.log)"
echo "1-bit presents after a font step: $(grep -c 'frame from B' $N.log)"
echo "declined-under-lock: $(grep -c 'armed the hold while' $N.log)"
