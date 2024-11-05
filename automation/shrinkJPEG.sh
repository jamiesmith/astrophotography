#!/bin/bash

function die_usage
{
    echo "Usage: $0 -Z size"
    echo " -z Max Size in pixels"
    echo "$*"
    exit 9
}

while getopts "z:" option
do
    case $option in
        z)
	        SIZE=$OPTARG
            ;;
	*)
	    die_usage "Wrong arg $option"
        
    esac
done
shift `expr $OPTIND - 1`

[ -n "$SIZE" ] || die_usage Size is required

for file in "$@"
do
    baseName="$(basename "$file" .jpg)"
    newName="${baseName}-${SIZE}.jpg"
    sips -Z $SIZE "$file" --out "$newName"
done