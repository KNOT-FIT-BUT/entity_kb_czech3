#!/bin/bash

set -o pipefail

cp -v ../HEAD-KB HEAD-KB &&
cp -v ../kb_sk kb_sk &&
cp -v ../VERSION VERSION &&
sed -i '$G' HEAD-KB &&
sed -i '/^$/d' HEAD-KB &&
sed -i '$G' HEAD-KB &&
python2 prepare_kb_to_stats_and_metrics.py < kb_sk | python2 check_columns_in_kb.py --cat | python2 wiki_stats_to_KB.py > KBstats.all &&
python2 metrics_to_KB.py -k KBstats.all | sed '/^\s*$/d' > KBstatsMetrics.all &&
# echo -n "VERSION=" | cat - VERSION HEAD-KB KBstatsMetrics.all > KB-HEAD.all &&
(mkdir ../outputs 2>/dev/null; (mv -v HEAD-KB ../outputs/ && mv -v KBstatsMetrics.all ../outputs/ && mv -v VERSION ../outputs/))
exit_status=$?

(( exit_status == 0 )) && rm kb_sk KBstats.all wiki_stats

exit $exit_status

