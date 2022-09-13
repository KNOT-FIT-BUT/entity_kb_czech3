#!/bin/bash

cd testing

out=`python person_tests.py 2>&1`
tail=`echo "$out" | tail -n 1`
if [[ $tail -eq "OK" ]]; then
	echo "[PERSON]	OK"
else
	echo "[PERSON]	FAIL"
	echo "$out"
fi

out=`python country_tests.py 2>&1`
tail=`echo "$out" | tail -n 1`
if [[ $tail -eq "OK" ]]; then
	echo "[COUNTRY]	OK"
else
	echo "[COUNTRY]	FAIL"
	echo "$out"
fi

out=`python settlement_tests.py 2>&1`
tail=`echo "$out" | tail -n 1`
if [[ $tail -eq "OK" ]]; then
	echo "[SETTLEMENT]	OK"
else
	echo "[SETTLEMENT]	FAIL"
	echo "$out"
fi