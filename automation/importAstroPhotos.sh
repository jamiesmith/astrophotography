#!/usr/local/bin/bash
shopt -s globstar
# This is not done.
#
baseDestDir="/Volumes/Astrophotography/AstroImages"
sourceDir=""

ECHO=""
ECHO="/bin/echo"

function die_usage
{
    echo "Usage: $0 -d | -m"
	echo " -d to import from dropbox"
	echo " -m to import from AstroMirror"
    echo "$*"
    exit 9
}

while getopts "dm" option
do
    case $option in
        d)
			sourceDir="/Users/jamie/Dropbox/AstroShedImages"
            ;;
        m)
			sourceDir="/Volumes/MIRRORIMAGE"            
            ;;
	*)
	    die_usage "Wrong arg $option"
        
    esac
done
shift `expr $OPTIND - 1`

[ -z "$sourceDir" ] && die_usage "error, must specify source"

cd ${sourceDir}

baseDateDir=""

for dateDir in $(ls -d 20??-??-??) 
do
    cd ${dateDir}

    # first the light frames
    #        
    find . -type f \( -iname "*LIGHT*.fits" ! -iname ".*" \) -print0 | sed 's|./||g' | while IFS= read -r -d '' file
    do
		oldName="${file}"
		target="${file%%_*}"
		
		newName="$(echo ${file} | sed 's| ||g;s|_NoTarget||g;s|${target}_${target}|${target}|g;s|${target}_FlatField|FlatField|g')"
		target="$(echo ${target} | sed 's| ||g')"

		destDir="${baseDestDir}/${target}/${dateDir}"

		echo "Copying ${newName} to ${target}/${dateDir}"

		# echo "target  : [${target}]"
		# echo "oldName : [${oldName}]"
		# echo "destDir : [${destDir}]"
		# echo "newName : [${newName}]"
		# echo ""

		mkdir -p "${destDir}"
		mkdir -p "${destDir}/processed"
		cp -p "${file}" "${destDir}/${newName}"
    done

    # Then the flats (this will need to change with NINA)
    #     
    find . -type f \( -iname "FLAT_*.fits" ! -iname ".*" \) -print0 | while IFS= read -r -d '' file    
    do
		oldName="${file}"
		newName="FLAT_${file##*FLAT_}"
		destDir="${baseDestDir}/${dateDir}/FLATS"

		# echo "file    : [${file}]"
		# echo "oldName : [${oldName}]"
		# echo "newName : [${newName}]"
		# echo "destDir : [${destDir}]"
		# echo ""
		# exit
		echo "Copying ${newName} to ${dateDir}"

		mkdir -p "${destDir}"
		cp -p "${file}" "${destDir}/${newName}"
    done

	echo DARK COPY IS NOT IMPLEMENTED
    # find . -type f \( -iname "*Dark*.fit" ! -iname ".*" \) -print0 | sed 's|./||g' | while IFS= read -r -d '' file
    # do
    #     oldName="${file}"
    #     newName="Dark_${file##*Dark_}"
    #
    #     destDir="${baseDestDir}/${dateDir}"
    #     echo "Copying ${newName} to ${dateDir}"
    #
    #     $ECHO mkdir -p "${destDir}"
    #     $ECHO cp -p "${file}" "${destDir}/${newName}"
    # done
    
    cd - > /dev/null   
done
