#!/usr/local/bin/bash

shopt -s globstar

# This is not done.
#
baseDestDir="/Volumes/Astrophotography/AstroImages"

sourceDir=""
projectDirSuffix="Project"
ECHO=""
ECHO="/bin/echo"
treeOnly=""

function die_usage
{
    echo "Usage: $0 -d | -m"
    echo " -d to import from dropbox"
    echo " -m to import from AstroMirror"
    echo " -o to override dest dir (currently ${baseDestDir})"
    echo " -t to just build the tree"
    echo "$*"
    exit 9
}

while getopts "dmo:t" option
do
    case $option in
        d)
            sourceDir="/Users/jamie/Dropbox/AstroShedImages"
            ;;
        m)
            sourceDir="/Volumes/MIRRORIMAGE"            
            ;;
        o)
            baseDestDir="$OPTARG"            
            ;;
        t)
            treeOnly="true"            
            ;;
        *)
            die_usage "Wrong arg $option"
        
    esac
done
shift `expr $OPTIND - 1`

[ -z "$sourceDir" ] && die_usage "error, must specify source via -m or -d"

cd ${sourceDir}

sessionDateDir=""

# Sample imported hierarchy for one night's targets
# Note that they get merged into the single date folders 
# (because some shots are after midnight)
# 
# ├── M42
# │   ├── 2023-11-18
# │   │   ├── LIGHTS
# │   │   │   └── < LIGHTS GO HERE >
# │   │   └── WBPP
# │   └── _M42-Project
# │       ├── CALIBRATED
# │       │   ├── 2023-11-18
# │       │   │   └── < CALIBRATED LIGHTS GO HERE >
# │       │   └── 2023-11-19
# │       │       └── < CALIBRATED LIGHTS GO HERE >
# │       └── WORK_AREA
# ├── M45
# │   ├── 2023-11-18
# │   │   ├── LIGHTS
# │   │   │   └── < LIGHTS GO HERE >
# │   │   └── WBPP
# │   └── _M45-Project
# │       ├── CALIBRATED
# │       │   ├── 2023-11-18
# │       │   │   └── < CALIBRATED LIGHTS GO HERE >
# │       │   └── 2023-11-19
# │       │       └── < CALIBRATED LIGHTS GO HERE >
# │       └── WORK_AREA
# └── RAW_CALIBRATION
#     └── 2023-11-18
#         └── FLATS
#             └── < FLATS GO HERE >

for dateDir in $(ls -d 20??-??-??) 
do
    if [ -z "${sessionDateDir}" ]
    then
        sessionDateDir="${dateDir}"
        echo "Setting session date to ${sessionDateDir}"
    fi
    
    cd ${dateDir}

    # first the light frames
    #        
    find . -type f \( -iname "*LIGHT*.fits" ! -iname ".*" \) -print0 | sed 's|./||g' | while IFS= read -r -d '' file
    do
        oldName="${file}"
        target="${file%%_*}"
        
        # newName="$(echo ${file} | sed 's| ||g;s|\x27||g;s|_NoTarget||g;s|${target}_${target}|${target}|g;s|${target}_FlatField|FlatField|g')"
        newName="$(echo ${file} | sed 's| ||g;s|\x27||g;s|${target}_FlatField|FlatField|g')"
        target="$(echo ${target} | cut -d "(" -f 1 | sed "s| ||g;s|'||g")"

        destDir="${baseDestDir}/${target}/${sessionDateDir}"
        projectDir="${baseDestDir}/${target}/_${target}-${projectDirSuffix}"   # The `_` keeps it first when sorted by name

        mkdir -p "${destDir}/LIGHTS"
        mkdir -p "${destDir}/WBPP"

        # this is to store longer, calibrated datasets
        #
        mkdir -p "${projectDir}/CALIBRATED/${sessionDateDir}"
        mkdir -p "${projectDir}/WORK_AREA"
        
        if [ -n "$treeOnly" ]
        then
            echo touch "${destDir}/LIGHTS/< LIGHTS GO HERE >"
            echo touch "${projectDir}/CALIBRATED/${sessionDateDir}/< CALIBRATED LIGHTS GO HERE >"
        else
            echo "Copying ${newName} to ${target}/${sessionDateDir}"
            cp -p "${file}" "${destDir}/LIGHTS/${newName}"
        fi
    done

    # Then the flats (this will need to change with NINA)
    #     
    find . -type f \( -iname "FLAT_*.fits" ! -iname ".*" \) -print0 | while IFS= read -r -d '' file
    do
        oldName="${file}"
        newName="FLAT_${file##*FLAT_}"
        destDir="${baseDestDir}/RAW_CALIBRATION/${sessionDateDir}/FLATS"


        mkdir -p "${destDir}"
        if [ -n "$treeOnly" ]
        then
            touch "${destDir}/< FLATS GO HERE >"
        else
            echo "Copying ${newName} to ${dateDir}"
            cp -p "${file}" "${destDir}/${newName}"
        fi

    done

    # echo DARK COPY IS NOT IMPLEMENTED
    # find . -type f \( -iname "DARK_*.fits" ! -iname ".*" \) -print0 | while IFS= read -r -d '' file
    # do
    #     oldName="${file}"
    #     newName="DARK_${file##*DARK_}"
    #     destDir="${baseDestDir}/RAW_CALIBRATION/${sessionDateDir}/DARKS"
    #
    #
    #     mkdir -p "${destDir}"
    #     if [ -n "$treeOnly" ]
    #     then
    #         touch "${destDir}/< DARKS GO HERE >"
    #     else
    #         echo "Copying ${newName} to ${dateDir}"
    #         cp -p "${file}" "${destDir}/${newName}"
    #     fi
    # done

    cd - > /dev/null   
done
