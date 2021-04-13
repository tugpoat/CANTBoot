#!/bin/bash
#extend roms parttion to end of disk
BLKDEV="/dev/mmcblk0"
CFG_PART_NUM=3
ROMS_PART_NUM=$(parted $BLKDEV -ms unit s p | tail -n 1 | cut -f 1 -d:)

echo "attempting to resize roms partition"

out=$(parted $BLKDEV --script u s print free)
checkval=$(echo $out | awk '{print $(NF-1),$NF}')

BLKDEV="${BLKDEV}p"

#just in case
umount $BLKDEV$CFG_PART_NUM
umount $BLKDEV$ROMS_PART_NUM


if [ "$checkval" == "Free Space" ]; then
	#we have free space at the end of the disk to expand into
	part_size=$(echo $out | awk '{print $(NF-8)}' | tr -d -c 0-9)
	echo "old partsize=$part_size"
	free_sectors=$(echo $out | awk '{print $(NF-2)}' | tr -d -c 0-9)
	echo "free sectors on disk=$free_sectors"
	new_size="$((($part_size+$free_sectors)*512))"
	echo "new partsize=$new_size"
	fatresize $BLKDEV$ROMS_PART_NUM -s $new_size
else
	echo "there was a problem with resizing the roms partition. this is a very descriptive error message. continuing anyways."
	#error
fi

mkdosfs -F 32 -I $BLKDEV$CFG_PART_NUM
mount $BLKDEV$CFG_PART_NUM -o rw /mnt/cfg
cp -r /home/naomi/CANTBoot/cfg/* /mnt/cfg
umount $BLKDEV$CFG_PART_NUM
#mount $BLKDEV$ROMS_PART_NUM -o rw /mnt/roms


#stop initial setup things from running next time
systemctl disable cantbootsetup.service
systemctl enable CANTBoot.service
echo "resized roms partition. rebooting"
reboot
#update-rc.d vsftpd remove
