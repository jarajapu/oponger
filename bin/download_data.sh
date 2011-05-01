#! /bin/bash
# Script to download all data from oponger into a timestamped CSV file
appcfg.py download_data --application=opingopong --url=http://opingopong.appspot.com/_ah/remote_api --filename=./data_backup_$(date +%Y%m%d-%H%M).csv
