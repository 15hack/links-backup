#!/bin/bash

while true; do
	cp data/webarchive_ko.txt ko.txt
	echo "" > data/webarchive_ko.txt
	sleep 5
	./webarchive.py
done
