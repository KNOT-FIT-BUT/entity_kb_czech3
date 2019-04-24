#/bin/bash
# Author: Tomas Volf, ivolf@fit.vutbr.cz

# default values
SAVE_PARAMS=$*

# saved values
LAUNCHED=$0

#=====================================================================
# nastavovani parametru prikazove radky

usage()
{
    echo "Usage: deploy.sh [PARAMETERS]"
    echo ""
    echo -e "  -h, --help   show this help message and exit"
    echo -e "  -u <login>   upload (deploy) KB to webstorage via given login"
    echo -e "               (default current user)"
    echo ""
}

DEPLOY=false

if test $# -eq 0
then
  usage
  exit
fi

while [ "$1" != "" ]; do
    PARAM=`echo $1 | awk -F= '{print $1}'`
#    VALUE=`echo $1 | awk -F= '{print $2}'`
    case $PARAM in
        -h | --help)
            usage
            exit
            ;;
        -u)
            DEPLOY=true
            VALUE=`echo $2`
            if test "${VALUE}" != "" -a "${VALUE:0:1}" != "-"
            then
                DEPLOY_USER=$VALUE
                shift
            else
                DEPLOY_USER=$USER
            fi
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


# Deploy new KB to server if it is required
if $DEPLOY
then
    DEPLOY_VERSION=`cat ./outputs/VERSION`
    DEPLOY_CONNECTION="${DEPLOY_USER}@athena3.fit.vutbr.cz"
    DEPLOY_FOLDER="/mnt/knot/www/NAKI_CPK/NER_CZ_inputs/kb/${DEPLOY_VERSION}"

    echo "Creating new folder: ${DEPLOY_FOLDER}"
    ssh "${DEPLOY_CONNECTION}" "mkdir -p \"${DEPLOY_FOLDER}\""
    echo "Upload files to new folder: ${DEPLOY_FOLDER}"
    scp outputs/* "${DEPLOY_CONNECTION}:${DEPLOY_FOLDER}"
    echo "Change symlink of new to this latest version of KB"
    ssh "${DEPLOY_CONNECTION}" "cd \"`dirname "${DEPLOY_FOLDER}"`\"; ln -sfT \"${DEPLOY_VERSION}\" new"
fi