#!/usr/local/bin/bash
# this is a seriously brute-force way to get image details...
# It's meant to be used specifically in a target base folder
# It makes a really bad assumption that all subs for a given filter are the same duration...

function getFilterID
{
    case $1 in
        Lum) 
            filterID=4543
            ;;
        Red) 
            filterID=4549
            ;;
        Green) 
            filterID=4537
            ;;
        Blue) 
            filterID=4531
            ;;
        Sii) 
            filterID=4526
            ;;
        Ha) 
            filterID=4517
            ;;
        Oiii) 
            filterID=4521
            ;;
        *)
            filterID=NA
    esac
    
    echo $filterID
}
filters="Lum Red Green Blue Sii Ha Oiii"

FORMATS="CSV SUMMARY"

echo "date,filter,number,duration"

declare -A total_time
declare -A total_count

for filter in $filters 
do
    total_time["$filter"]=0
    total_count["$filter"]=0
done

overall_total_time=0
overall_total_subs=0

for format in $FORMATS
do
    if [ "$format" = "CSV" ]
    then
        echo "CSV Summary, suitable for Astrobin"
        echo ""
    fi

    for date in 20*
    do
        if [ "$format" = "SUMMARY" ]
        then
            echo ${date}:
        fi
        
        cd $date/LIGHTS

        for filter in $filters 
        do
            count=$(find . -name \*.fits -o -name \*.xisf -maxdepth 3| grep -c $filter)
            if [ $count -gt 0 ]
            then
                sample=$(find . -name \*.fits -o -name \*.xisf | grep $filter|head -1)
                sample=$(basename $sample)
                exposureDuration=$(echo $sample | cut -d"_" -f 2 | sed 's|.00secs||g')
                totalSeconds=$(($count * $exposureDuration))
                dateHours=$(bc -l <<< "$count * $exposureDuration / 3600")
                
                # date=
                filterID=$(getFilterID $filter)
                number=$count
                duration=$exposureDuration

                if [ "$format" = "CSV" ]
                then
                    printf "%s,%s,%s,%s\n" \
                        "${date}" \
                        "${filterID}" \
                        "${number}" \
                        "${duration}"
                else
                    total_time[$filter]=$((${total_time[$filter]}+$totalSeconds))
                    total_count[$filter]=$((${total_count[$filter]}+$count))
                    overall_total_time=$((${overall_total_time}+$totalSeconds))
                    overall_total_subs=$((${overall_total_subs}+$count))
                    printf "\t%-5s: %i @%s secs / %.2f hours\n" $filter $count $exposureDuration $dateHours
                fi
            fi
        done    
        cd ../..
    done
    echo ""
    if [ "$format" = "SUMMARY" ]
    then
        printf "Per-filter totals:\n"
        for filter in $filters 
        do
            total=$(bc -l <<< "${total_time[$filter]} / 3600")
            printf "\t%-6s: %6.2f hours (%i subs)\n" $filter $total ${total_count[$filter]} 
            # echo $filter ${total_time[$filter]}
        done
        overall_total=$(bc -l <<< "$overall_total_time / 3600")
        printf "\ttotal : %6.2f hours (%i subs)\n" $overall_total $overall_total_subs
    fi
    
done
