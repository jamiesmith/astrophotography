#!/bin/ksh

function dirsync
{
    echo Synchronizing $1 to $2
	rsync --verbose \
		--size-only \
		--archive \
		--update \
        --exclude "@Focus3 Runs" \
        --exclude "@Focus2 Runs" \
        --exclude "Closed Loop Slews" \
		--exclude ".Trashes" \
		--exclude ".Spotlight-V100" \
		--exclude "astrophotography" \
		--exclude "Automated*" \
		"$1" "$2"
}

# All of the astro images, twice.
#
while [ 1 ]
do
    dirsync "/Volumes/AstroImages/" "/Volumes/MIRRORIMAGE"
    # dirsync "/Volumes/AstroImages/" "/Users/jamie/AstroMirror"
    # Sync to dropbox instead
    # dirsync "/Volumes/MIRRORIMAGE/" "/Users/jamie/AstroMirror/"
    #
    dirsync "/Volumes/MIRRORIMAGE/" "/Users/jamie/Dropbox/AstroShedImages/"    
    sleep 10
done
