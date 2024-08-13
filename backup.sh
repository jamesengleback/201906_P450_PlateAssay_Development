#/bin/bash

OUTDIR='db-checkpoints'
FILENAME='db.sqlite3'

if ! [ -d $OUTDIR ]; then
                    mkdir $OUTDIR ;
fi;

if [ -f $FILENAME ]; then
                    cp $FILENAME $OUTDIR/db-"$(date '+%Y-%m-%d:%H:%M').sqlite3" ;
fi;
