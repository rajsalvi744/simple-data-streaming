#!/bin/sh

file_path="/tmp/clusterID/clusterID"
interval=5  # wait interval in seconds

while [ ! -e "$file_path" ] || [ ! -s "$file_path" ]; do
  echo "Waiting for $file_path to be created..."
  sleep $interval
done

cat "$file_path"
# KRaft required step: Format the storage directory with a new cluster ID
echo "export CLUSTER_ID=$(cat "$file_path")" >> /etc/confluent/docker/bash-config
