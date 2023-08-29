#!/usr/local/bin/bash
shopt -s globstar
# This is not done.
#
baseDestDir="/Volumes/Astrophotography/AstroImages"
sourceDir=""


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

for dateDir in $(ls -d 20??-??-??) 
do
    pwd
    echo ${dateDir}
    cd ${dateDir}

    # first the light frames
    #        
    find . -type f \( -iname "*Light*.fit" ! -iname ".*" \) -print0 | sed 's|./||g' | while IFS= read -r -d '' file
    do
       oldName="${file}"
       target="${file%%-*}"
    
       newName="$(echo ${file} | sed "s|-NoTarget||g;s|${target}-${target}|${target}|g;s|${target}-FlatField|FlatField|g")"
    
       destDir="${baseDestDir}/${target}/${dateDir}"

       echo "Copying ${newName} to ${target}/${dateDir}"
    
       mkdir -p "${destDir}"
       mkdir -p "${destDir}/processed"
       cp -p "${file}" "${destDir}/${newName}"
    done

    find . -type f \( -iname "*FlatField*.fit" ! -iname ".*" \) -print0 | sed 's|./||g' | while IFS= read -r -d '' file    
    do
        oldName="${file}"
        newName="FlatField_${file##*FlatField_}"

        if [[ "${file}" == *"adu"* ]]
        then
            destDir="${baseDestDir}/${dateDir}"
            echo "Copying ${newName} to ${dateDir}"

            mkdir -p "${destDir}"
            cp -p "${file}" "${destDir}/${newName}"
        else
            echo "#### Skipping bad flat ${file}"
        fi
        
    done
    
    find . -type f \( -iname "*Dark*.fit" ! -iname ".*" \) -print0 | sed 's|./||g' | while IFS= read -r -d '' file    
    do
        oldName="${file}"
        newName="Dark_${file##*Dark_}"

        destDir="${baseDestDir}/${dateDir}"
        echo "Copying ${newName} to ${dateDir}"

        mkdir -p "${destDir}"
        cp -p "${file}" "${destDir}/${newName}"
    done
    
    cd - > /dev/null   
done
