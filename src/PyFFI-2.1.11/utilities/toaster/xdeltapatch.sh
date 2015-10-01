#!/bin/sh
# $1=old, $2=new, $3=patch
old=$1
new=$2
patch=$3
shift 3
xdelta patch $@ $patch $old $new
