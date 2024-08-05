#!/bin/bash

filters="Lum Red Green Blue Sii Ha Oiii"

for filter in $filters 
do
    
    count=$(find . -name \*.fits -o -name \*.xisf | grep -c $filter)
    if [ $count -gt 0 ]
    then
        sample=$(find . -name \*.fits -o -name \*.xisf | grep $filter|head -1)
        sample=$(basename $sample)
        exp=$(echo $sample | cut -d"_" -f 2 | sed 's|.00secs||g')
        total=$(bc -l <<< "$count * $exp / 3600")
        printf "%-5s: %i [%s] %f hours\n" $filter $count $exp $total
    fi
done    
