#!/bin/bash

cd scheduler/repo

for branch in "$@"
do
    if ! git show-ref --verify --quiet refs/heads/$branch; then
        echo "Branch $branch does not exist."
        exit 1
    fi

    if ! git checkout $branch --quiet; then
        echo "Cannot checkout branch $branch. You have uncommitted changes."
        exit 1
    fi
    git checkout -
done

for branch in "$@"
do
    git checkout $branch

    cd ../..

    ./run_name.sh 2>&1 | tee log.txt &
    pid=$!

    while ! tail -n 100 log.txt | grep -q "simulator-1 exited with code"
    do
        sleep 1
    done

    kill -9 $pid
    wait $pid 2>/dev/null
    rm log.txt
    cd scheduler/repo
done

cd ../..