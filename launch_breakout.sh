#!/bin/bash
export DISPLAY=:0
export XAUTHORITY=/home/pi/.Xauthority
cd /home/pi/VSCodeProjects/breakout
/usr/bin/python breakout.py
