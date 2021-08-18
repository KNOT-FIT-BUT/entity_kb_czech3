#!/usr/bin/env python
# -*- coding: utf-8 -*-

# IMPORTANT!!! it is needed to run export PYTHONIOENCODING=UTF-8 before this

import argparse
import datetime
import pickle
import regex
import sys

from ast import literal_eval


LITERAL_EVAL_ERR_SEEK = 'EOL while scanning string literal'
dt = datetime.datetime.now()

parser = argparse.ArgumentParser()
parser.add_argument('-d', '--dump-version', type = str, default = '{}{:02d}01'.format(dt.year, dt.month), help = 'Dump version of geo tags (default: %(default)s).')
parser.add_argument('-o', '--output', type = str, default = 'geo_tags.pkl', help = 'Output file with geo tags of entity.')
args = parser.parse_args()

with open('cswiki-{}-geo_tags.sql'.format(args.dump_version), 'r', encoding = 'utf-8', errors = 'ignore') as f:
  gt_content = f.read()

head = regex.search('CREATE\s+TABLE\s+[^\(]+?\(.*?\)[^\(\)]*?;', gt_content, regex.IGNORECASE | regex.DOTALL)
if not head:
  print('ERROR: Unknown format of input (header).', file = sys.stderr)
  sys.exit(1)
head = regex.findall('(?<=^\s*\`)[^\`]+?(?=\`)', head.group(0), regex.MULTILINE)

name = head.index('gt_name')
lat = head.index('gt_lat')
lon = head.index('gt_lon')
tmp_globe = head.index('gt_globe')
tmp_primary = head.index('gt_primary')
n_head_cols = len(head)

outdata = dict()
inserts = regex.findall("(?<=VALUES\s+\()(.*?)\);", gt_content, regex.IGNORECASE | regex.DOTALL)

if len(inserts) == 0:
  print('ERROR: Unknown format of input (data).', file = sys.stderr)
  sys.exit(2)

for insert_line in inserts:
  indata = insert_line.split('),(')
  for x, item in enumerate(indata):
    item_cols = item.split(',')
    while (len(item_cols) > n_head_cols):
      item_cols[name] += item_cols[name + 1]
      del item_cols[name + 1]
    for i_ic, ic in enumerate(item_cols):
      try:
        item_cols[i_ic] = literal_eval(ic) if ic != 'NULL' else None
      except Exception as e:
        print('ERROR WHILE RECOGNIZING ORIGINAL DATA TYPE: {}'.format(e.args[0]), file = sys.stderr)
        sys.exit()

    if item_cols[tmp_globe] == 'earth' and item_cols[tmp_primary] == 1:
      outdata[item_cols[name].strip('\'')] = {'lat': item_cols[lat], 'lon': item_cols[lon]}

with open(args.output, 'wb') as fout:
  pickle.dump(outdata, fout)