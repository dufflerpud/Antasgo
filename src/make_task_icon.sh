#!/bin/sh

PROG=`basename $0`
TMP=/tmp/$PROG		# or /tmp/$PROG.$$

#########################################################################
#	Print usage message and exit.					#
#########################################################################
usage()
    {
    echo "$*" | tr '~' '\012'
    echo "Usage:  $PROG file"
    exit 1
    }

#########################################################################
#	Print command and then execute it.				#
#########################################################################
echodo()
    {
    echo "+ $*"
    eval "$@"
    }

#########################################################################
#	Main								#
#########################################################################

# Parse arguments
while [ "$#" -gt 0 ] ; do
    case "$1" in
    	#*)	PROBLEMS="${PROBLEMS}Illegal argument [$1].~"	;;
    	*.png)	if [ -z "$INFILE" ] ; then
		    INFILE="$1"
		    if [ ! -r "$INFILE" ] ; then
		        PROBLEMS="${PROBLEMS}$INFILE does not exist.~"
		    fi
		elif [ -z "$OUTFILE" ] ; then
		    OUTFILE="$1"
		else
		    PROBLEMS="${PROBLEMS}Too many files specified [$1].~"
		fi
		;;
    	*.*)	if [ -z "$INFILE" ] ; then
		    INFILE="$1"
		else
		    PROBLEMS="${PROBLEMS}Output file must be a .png file [$1].~"
		fi
		;;
	*)	PROBLEMS="${PROBLEMS}Filenames require extensions [$1].~"
		;;
    esac
    shift
done

[ -n "$PROBLEMS" ] && usage "$PROBLEMS"

nene "$INFILE" -.pnm \
	| pamscale -width=100 \
	| convert - -fuzz 20% -transparent white $OUTFILE

exit 0
