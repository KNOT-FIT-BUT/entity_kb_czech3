#!/bin/bash
# Author: Tomas Volf, ivolf@fit.vutbr.cz

# TODO: -g, -p, -r processing

export LC_ALL="C.UTF-8"

# default values
SAVE_PARAMS=$*
LOG=false
LANG=cs
DUMP_PATH=/mnt/minerva1/nlp/corpora/monolingual/czech/wikipedia/
DUMP_VERSION=latest
STATS_PATH=/mnt/minerva1/nlp-in/wikipedia-statistics/stats

# saved values
LAUNCHED=$0

NPROC=`nproc || echo 1`
GB_THRESHOLD=10
FREE_MEMORY=$((`awk '/Mem(Available|Free)/ { data = $2 > data ? $2 : data } END { printf "%.0f \n", data/1024/1024 }' /proc/meminfo`))
NPROC=$((FREE_MEMORY / NPROC >= GB_THRESHOLD ? NPROC : FREE_MEMORY / GB_THRESHOLD))

if test "$NPROC" -lt 1
then
  NPROC=1
fi

#=====================================================================
# nastavovani parametru prikazove radky

usage()
{
    DUMP_PATH="${DUMP_PATH})"
    cut_DUMP_PATH=$((`tput cols` - 25))
    echo "Usage: start.sh [PARAMETERS]"
    echo ""
    echo -e "  -h, --help   show this help message and exit"
    echo ""
    echo -e "OPTIONAL arguments:"
    echo -e "  -l <lang>    language of wikipedia dumps to process (default: ${LANG})"
    echo -e "  -m <int>     number of pool processes to parallelize entities processing (default: ${NPROC})"
    echo -e "  -d <version> version of dumps to process (default: ${DUMP_VERSION})"
    echo -e "  -I <path>    set a dir path of wikipedia dump files serving as input for KB creation purposes"
    echo -e "               (default: ${DUMP_PATH::${cut_DUMP_PATH}}"
    if test $cut_DUMP_PATH -lt ${#DUMP_PATH}
    then
        echo -e "               ${DUMP_PATH:${cut_DUMP_PATH}}"
    fi
    echo -e "  -u [<login>] upload (deploy) KB to webstorage via given login"
    echo -e "               (default current user)"
    echo -e "  --dev        Development mode (upload to separate space to prevent forming a new production/stable version of KB)"
    echo -e "  --test       Test mode (upload to separate space to prevent forming a new production/stable version of KB)"
    echo -e "  --log        log to start.sh.stdout, start.sh.stderr and start.sh.stdmix"
#    echo ""
#    echo -e "MULTIPLE DUMP PATHS CUSTOMIZATION:"
#    echo -e "  -g <path>    set a path of wikipedia geo tags dump file input"
#    echo -e "  -p <path>    set a path of wikipedia pages dump file input"
#    echo -e "  -r <path>    set a path of wikipedia redirects dump file input"
    echo ""
}

CUSTOM_DUMP_PATH=false
CUSTOM_REDIR_PATH=false
REDIR_PATH=
DEPLOY=false
MULTIPROC_PARAMS="-m ${NPROC}"
EXTRACTION_ARGS=()
KB_STABILITY=

while [ "$1" != "" ]; do
    PARAM=`echo $1 | awk -F= '{print $1}'`
    VALUE=`echo $1 | awk -F= '{print $2}'`
    case $PARAM in
        -h | --help)
            usage
            exit
            ;;
        -d)
            DUMP_VERSION=$2
            shift
            ;;
        -I)
            CUSTOM_DUMP_PATH=true
            DUMP_PATH=$2
            shift
            ;;
        -l)
            LANG=$2
            shift
            ;;
#        -r)
#            CUSTOM_REDIR_PATH=true
#            REDIR_PATH=$2
#            shift
#            ;;
        -m)
            MULTIPROC_PARAMS="-m ${2}"
            shift
            ;;
        -u)
            DEPLOY=true
            LOGIN=$2
            if test "${LOGIN:0:1}" = "-"
            then
                DEPLOY_USER=`whoami`
            else
                DEPLOY_USER=$2
                shift
            fi
            ;;
        --dev)
            KB_STABILITY="--dev"
            ;;
        --test)
            if test -z "${KB_STABILITY}"
            then
              KB_STABILITY="--test"
            fi
            ;;
        --log) LOG=true
            ;;
        *)
            >&2 echo "ERROR: unknown parameter \"$PARAM\""
            usage
            exit 1
            ;;
    esac
    shift
done

# zmena spousteci cesty na tu, ve ktere se nachazi start.sh
cd `dirname "${LAUNCHED}"`

if $LOG; then
	rm -f start.sh.fifo.stdout start.sh.fifo.stderr start.sh.fifo.stdmix
	mkfifo start.sh.fifo.stdout start.sh.fifo.stderr start.sh.fifo.stdmix

	cat start.sh.fifo.stdout | tee start.sh.stdout > start.sh.fifo.stdmix &
	cat start.sh.fifo.stderr | tee start.sh.stderr > start.sh.fifo.stdmix &
	cat start.sh.fifo.stdmix > start.sh.stdmix &
	exec > start.sh.fifo.stdout 2> start.sh.fifo.stderr
fi

DUMP_DIR=`dirname "${DUMP_PATH}"`

# If Wikipedia dump path is symlink, then read real path
if test -L "${DUMP_PATH}"
then
    DUMP_PATH=`readlink "${DUMP_PATH}"`
    if test `dirname "${DUMP_PATH}"` = "."
    then
        DUMP_PATH="${DUMP_DIR}/${DUMP_PATH}"
    fi
fi

# Test file existence and zero-length of file
#if test ! -s "${DUMP_PATH}" -o ! -r "${DUMP_PATH}"
#then
#    >&2 echo "ERROR: wikipedia pages dump file does not exist or is zero-length"
#    exit 2
#fi

# If custom redirects path was not set, extract the default one
#if ! ${CUSTOM_REDIR_PATH}
#then
#    REDIR_PATH="`dirname "${DUMP_PATH}"`/redirects_from_`basename "${DUMP_PATH}"`"
#fi

# Extract Wikipedia dump file version number
#VERSION=`basename "${DUMP_PATH}" | sed 's/^.*\([0-9]\{8\}\).*$/\1/'`
#if test ${#VERSION} -ne 8
#then
#    >&2 echo "ERROR: can not parse version info from path - name of input file must contain 8-digit (date) version info"
#    exit 3
#fi

EXTRACTION_ARGS+=(${KB_STABILITY})
EXTRACTION_ARGS+=(${MULTIPROC_PARAMS})

# Run CS Wikipedia extractor to create new KB
CMD="python3 wiki_cs_extract.py --lang ${LANG} --dump ${DUMP_VERSION} --indir \"${DUMP_PATH}\" ${EXTRACTION_ARGS[@]} 2>entities_processing.log"
echo "RUNNING COMMAND: ${CMD}"
eval $CMD

F_KB_INCONSISTENCES=kb_inconsistences.tsv
echo -e "ENTITY NAME\tTYPE\tCOLUMN\tOLD VALUE\tNEW VALUE\tCAME FROM" > "${F_KB_INCONSISTENCES}"
cat entities_processing.log | grep "\[INCONSISTENCE CHECK\]" | grep "Error:" | sed -E "s/^.*for\s+\"([^\"]+)\".*type\s+\"([^\"]+)\".*item\s+\"([^\"]+)\".*old=\"([^\"]+)\".*new=\"([^\"]+)\"(\s+\(new\s+value\s+came\s+from\s+([^\)]+)\))?.*$/\1\t\2\t\3\t\4\t\5\t\7/g" >> "${F_KB_INCONSISTENCES}"
echo >> "${F_KB_INCONSISTENCES}"
# [INCONSISTENCE CHECK] Warning: New value="{new}" maybe should be in KB for item "{column}" of "{self.original_title}" (of type "{self.prefix}")? Old value="{old}" remains in KB.{origin}
cat entities_processing.log | grep "\[INCONSISTENCE CHECK\]" | grep "Warning:" | sed -E "s/^.*New\s+value=\"([^\"]+)\".*item\s+\"([^\"]+)\"\s+of\s+\"([^\"]+)\".*type\s+\"([^\"]+)\".*Old\s+value=\"([^\"]+)\".*in\s+KB.(\s+\(new\s+value\s+came\s+from\s+([^\)]+)\))?.*$/\3\t\4\t\2\t\5\t\1\t\7/g" >> "${F_KB_INCONSISTENCES}"

OUTDIR="outputs"
mkdir -p "${OUTDIR}"

# Convert Wikipedia KB format to Generic KB format
python3 kbwiki2gkb.py --inkb "kb_cs" --outdir "${OUTDIR}"

# Add stats to KB and compute metrics
mkdir -p outputs
python3 wikipedia_stats/stats_to_kb.py --input "outputs/KB.tsv" --output "outputs/KB+stats.tsv" -pw "$STATS_PATH/pageviews/latest_cs_pageviews.tsv" -bps "$STATS_PATH/bps/latest_cs_bps.tsv"

if $DEPLOY
then
    ./deploy.sh -u $DEPLOY_USER
fi
