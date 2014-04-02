#!/usr/bin/env bash
set -ue

ARGFILE="default.args"
USAGE="\$ $(basename $0) [client-id]
This is a crazy, hacky way of retrieving and formatting your current Imgur API
limits. If no client-id is provided, it will read it from the default argument
file "'"'$ARGFILE'".'

if [[ $# -gt 0 ]]; then
  if [[ $1 == '-h' ]]; then
    echo "$USAGE"
    exit 1
  fi
  clientid=$1
else
  script_dir=$(dirname $0)
  clientid=$(grep -A 1 -- '--client-id' "$script_dir/$ARGFILE" | tail -n 1)
fi

if [[ ! $clientid ]]; then
  echo "Error: could not get client id" >&2
  exit 1
fi

response=$(curl -H "Authorization:Client-ID $clientid" 'https://api.imgur.com/3/credits' 2>/dev/null)

response=$(echo "$response" | sed -e 's/"//g' -e 's/{data:{//' -e 's/}.*//')

response=$(echo "$response" | sed 's/:/\t/g')

echo "$response" | tr ',' '\n' | while read line; do
  timestamp=$(echo "$line" | sed -nE 's/^UserReset\s+([0-9]+)$/\1/p')
  if [[ $timestamp ]]; then
    time=$(date -d @$timestamp)
    echo "$line" | sed "s/$timestamp/$time/"
  else
    echo "$line"
  fi
done
