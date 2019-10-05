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
    sleep 10
    dirsync "/Volumes/AstroImages" "/Volumes/AstroMirror"
    dirsync "/Volumes/AstroImages" "/Volumes/MIRRORIMAGE"
    
done