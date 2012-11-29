#!/bin/bash

if [ "`whoami`" != "root" ]; then
    echo "Not root, can't do anything"
    exit 1
fi

LIDLINE=`cat /proc/acpi/wakeup | grep "LID0"`
echo "Lid line is: ${LIDLINE}"
if echo $LIDLINE | grep -q 'enabled'; then
    echo "Found enabled!"
    echo "LID0" > /proc/acpi/wakeup
    echo "Should be disabled now"
else
    echo "Either lid line wasn't there, or it was already disabled...not doing anything with the lid switch!"
fi

echo "Now suspending..."
pm-suspend
