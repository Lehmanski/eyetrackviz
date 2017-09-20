##!/bin/bash
# Extract subtitles from each MKV file in the given directory

# If no directory is given, work in local dir
if [ "$1" = "" ]; then
  DIR="."
else
  DIR="$1"
fi

# Get all the MKV files in this dir and its subdirs
find "$DIR" -type f -name '*.mkv' | while read filename
do
  # Find out which tracks contain the subtitles
  mkvmerge -i "$filename" | grep 'subtitles' | while read subline
  do
    # Grep the number of the subtitle track
    tracknumber=`echo $subline | egrep -o "[0-9]{1,2}" | head -1`

    # Get base name for subtitle
    subtitlename=${filename%.*}

    # Extract the track to a .tmp file
    `mkvextract tracks "$filename" $tracknumber:"$subtitlename.ass.tmp" > /dev/null 2>&1`
    `chmod g+rw "$subtitlename.ass.tmp"`

    # Do a super-primitive language guess: DUTCH
    langtest=`egrep -ic ' ik | je | een ' "$subtitlename".ass.tmp`
    trimregex="vertaling &\|vertaling:\|vertaald door\|bierdopje"

    # Do a super-primitive language guess: ENGLISH
    #langtest=`egrep -ic ' you | to | the ' "$subtitlename".ass.tmp`
    #trimregex=""

    # Do a super-primitive language guess: GERMAN
    #langtest=`egrep -ic ' ich | ist | sie ' "$subtitlename".ass.tmp`
    #trimregex=""

    # Do a super-primitive language guess: SPANISH
    #langtest=`egrep -ic ' el | es | por ' "$subtitlename".ass.tmp`
    #trimregex=""

    # Check if subtitle passes our language filter (10 or more matches)
    if [ $langtest -ge 10 ]; then
      # Regex to remove credits at the end of subtitles (read my reason why!)
      `sed 's/\r//g' < "$subtitlename.ass.tmp" \
        | sed 's/%/%%/g' \
        | awk '{if (a){printf("\t")};printf $0; a=1; } /^$/{print ""; a=0;}' \
        | grep -iv "$trimregex" \
        | sed 's/\t/\r\n/g' > "$subtitlename.ass"`
      `rm "$subtitlename.ass.tmp"`
      `chmod g+rw "$subtitlename.ass"`
    else
      # Not our desired language: add a number to the filename and keep anyway, just in case
      `mv "$subtitlename.ass.tmp" "$subtitlename.$tracknumber.ass" > /dev/null 2>&1`
    fi
  done
done
