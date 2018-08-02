#!/bin/bash
# Copyright (c) 2017 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
ipmitool="/usr/bin/ipmitool"

if [ -z $IPMI_PASSWORD ]; then
	echo $0: IPMI_PASSWORD environment has to be set
	exit 1
elif [ $# -le 1 ]; then
	echo $0 -b disk -r -f FILENAME
	echo "$0: Parameters";echo
	echo "-b (disk|pxe)	- boot from (order)"
	echo "-r		- reboot"
	echo "-f		- file containg ips and/or hostnames"
	echo "Example: $0 -b pxe -r -f server.list.txt"
	echo; echo "IPMI password is extracted from IPMI_PASSWORD environment"
	exit 1
elif [ ! -f $ipmitool ];  then
	echo "$0: install ipmitool package"
	exit 1
fi

OPTIND=1
boot_first="null"
file=""
reboot=0
# getops
while getopts "b:f:r" arg; do
	case "$arg" in
	b)
		boot_first=$OPTARG
		;;
	f)
		file=$OPTARG
		;;
	r)
		reboot=1
		;;
	\?)
		exit 1
		;;
	esac
done
shift $((OPTIND-1))

if [ ! -f $file ]; then
	echo "$0: provide file with the list of IPMI endpoints"
	exit 1
elif [ `wc -l $file|awk '{print $1}'` -gt 0 ]; then
	echo "boot first:	$boot_first"
	echo "file:		$file"
	echo "reboot:		$reboot"

	for server in `grep -v ^\# $file`; do
		if [ $boot_first = "disk" -o $boot_first = "pxe" ]; then
			echo "$0: changing primary boot device for $server"
			$ipmitool -I lanplus -H $server -U root -E chassis bootdev $boot_first
		fi
		if [ $reboot -eq 1 ]; then
			echo "$0: rebooting $server"
			$ipmitool -I lanplus -H $server -U root -E power cycle
		fi
	done
else
	echo "$0: unexpected script execution; empty or non-existing file."
	exit 1
fi
