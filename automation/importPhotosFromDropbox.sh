#!/bin/bash

# This is not done.
#
sourceDir="$(pwd)"
baseDestDir="/Volumes/Astrophotography/AstroImages"

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
       echo "Copying ${newName} to ${dateDir}/${target}"
    
       mkdir -p "${destDir}"
       cp -p "${file}" "${destDir}/${newName}"
    done
    #
    # find . -type f \( -iname "*FlatField*.fit" ! -iname ".*" \) -print0 | sed 's|./||g' | while IFS= read -r -d '' file
    # do
    #     oldName="${file}"
    #     newName="FlatField_${file##*FlatField_}"
    #
    #     if [[ "${file}" == *"adu"* ]]
    #     then
    #         destDir="${baseDestDir}/${dateDir}"
    #         echo "Copying ${newName} to ${dateDir}"
    #
    #         mkdir -p "${destDir}"
    #         cp -p "${file}" "${destDir}/${newName}"
    #     else
    #         echo "#### Skipping bad flat ${file}"
    #     fi
    #
    # done
    #
    # find . -type f \( -iname "*Dark*.fit" ! -iname ".*" \) -print0 | sed 's|./||g' | while IFS= read -r -d '' file
    # do
    #     oldName="${file}"
    #     newName="Dark_${file##*Dark_}"
    #
    #     destDir="${baseDestDir}/${dateDir}"
    #     echo "Copying ${newName} to ${dateDir}"
    #
    #     mkdir -p "${destDir}"
    #     cp -p "${file}" "${destDir}/${newName}"
    # done
    
    cd - > /dev/null   
done
