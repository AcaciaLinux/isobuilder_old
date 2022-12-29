import os
import shutil

from log import blog
from initramfs import initramfs
from envmanager import envmanager

BUILD_DIRECTORY = "build"
SOURCE_DIRECTORY = "bootfiles"

SOURCE_FILES = [ "bootlogo.png", "syslinux.cfg", "extlinux.x64", "isolinux.bin", "ldlinux.c32", "libcom32.c32", "libutil.c32", "vesamenu.c32" ]
CORE_FS = "/bin /etc /home /lib /lib64 /opt /root /sbin /srv /usr /var /sys /dev /proc /run /tmp"

def copy_from_source(file):
    if(not os.path.exists(os.path.join(SOURCE_DIRECTORY, file))):
        return -1
    
    boot_path = os.path.join(BUILD_DIRECTORY, "boot")

    shutil.copy(os.path.join(SOURCE_DIRECTORY, file), os.path.join(boot_path, file))
    return 0

def build_iso():
    blog.info("Creating build directory..")
    
    if(os.path.exists(BUILD_DIRECTORY)):
        blog.warn("Removing old build directory..")
        shutil.rmtree(BUILD_DIRECTORY)

    os.makedirs("build/boot")

    blog.info("Copying boot files..")
    for f in SOURCE_FILES:
        if(copy_from_source(f) != 0):
            blog.error("Could not find {} in bootfiles directory. Aborting.".format(f))
            return -1

    blog.info("Copying initramfs..")
    shutil.copy(initramfs.TARGET_FILE, os.path.join(BUILD_DIRECTORY, initramfs.TARGET_FILE))

    blog.info("Copying kernel image..")
    shutil.copy(os.path.join(envmanager.BUILD_ROOT_DIR, "boot/vmlinuz-acacia-lts"), os.path.join(BUILD_DIRECTORY, "vmlinuz-acacia-lts"))

    blog.info("Generating squashfs..")
    os.system("chroot {} mksquashfs {} /01-core.sb -comp xz -b 1024K -always-use-fragments -keep-as-directory -processors $(nproc)".format(envmanager.BUILD_ROOT_DIR, CORE_FS))
    
    blog.info("Moving squashfs to build directory..")
    shutil.move(os.path.join(envmanager.BUILD_ROOT_DIR, "01-core.sb"), os.path.join(BUILD_DIRECTORY, "01-core.sb"))

    blog.info("Creating bootable ISO image..")
    os.system("mkisofs -o AcaciaLinux.iso -v -J -R -D -A \"AcaciaLinux\" -V AcaciaLinux -no-emul-boot -boot-info-table -boot-load-size 4 -b \"boot/isolinux.bin\" -c \"boot/isolinux\" {}".format(BUILD_DIRECTORY))
    return 0
