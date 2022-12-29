qemu-system-x86_64 \
	-enable-kvm \
	-m 1024 \
	-kernel ./buildroot/boot/vmlinuz-acacia-lts \
	-initrd acacia-initrd.img \
	-append "rw initrdshell load_ramdisk=1 prompt_ramdisk printk.time=0 debug init=/init" # might not need init=/init
