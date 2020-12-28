#extend roms parttion to end of disk
BLKDEV="/dev/sda"
CFG_PART_NUM=3
PART_NUM=$(parted $BLKDEV -ms unit s p | tail -n 1 | cut -f 1 -d:)

#just in case
umount $BLKDEV$CFG_PART_NUM
umount $BLKDEV$PART_NUM

out=$(parted $BLKDEV --script u s print free)
checkval=$(echo $out | awk '{print $(NF-1),$NF}')
echo $checkval
if [[ $checkval -eq "Free Space" ]]; then
	#we have free space at the end of the disk to expand into
	part_size=$(echo $out | awk '{print $(NF-8)}' | tr -d -c 0-9)
	free_sectors=$(echo $out | awk '{print $(NF-2)}' | tr -d -c 0-9)
	new_size="$((($part_size+$free_sectors)*512))"
	fatresize $BLKDEV$PART_NUM -s $new_size
else
	#error
fi

mkdosfs -F 32 -I $BLKDEV$CFG_PART_NUM
mount $BLKDEV$CFG_PART_NUM -o rw /mnt/cfg
cp -r /home/naomi/CANTBoot/cfg/* /mnt/cfg
mount $BLKDEV$PART_NUM -o rw /mnt/roms


#stop initial setup things from running next time
systemctl cantbootsetup disable

update-rc.d vsftpd remove
