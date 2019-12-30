#!/bin/ksh

function dirsync
{
	rsync --verbose \
		--size-only \
		--archive \
		--update \
		"$1" "$2"
}

# All of the astro images, twice.
#
while [ 1 ]
do
    dirsync "/Volumes/AstroImages/" "/Users/jamie/AstroMirror"
    dirsync "/Volumes/AstroImages/" "/Volumes/MIRRORIMAGE"
    sleep 10
done