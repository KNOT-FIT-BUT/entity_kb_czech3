#!/bin/bash

set -o pipefail

cp -v ../HEAD-KB HEAD-KB &&
cp -v ../kb_cs kb_cs &&
sed -i '$G' HEAD-KB &&
sed -i '/^$/d' HEAD-KB &&
sed -i '$G' HEAD-KB &&
date +%s > VERSION &&
python2 prepare_kb_to_stats_and_metrics.py < kb_cs | python2 check_columns_in_kb.py --cat | python2 wiki_stats_to_KB.py > KBstats.all &&
python2 metrics_to_KB.py -k KBstats.all | sed '/^\s*$/d' > KBstatsMetrics.all &&
echo -n "VERSION=" | cat - VERSION HEAD-KB KBstatsMetrics.all > KB-HEAD.all
exit_status=$?

(( exit_status == 0 )) && rm KBstats.all wiki_stats

exit $exit_status

