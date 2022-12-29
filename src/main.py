import os

from log import blog
from envmanager import envmanager
from initramfs import initramfs
from squash import squash

KNAME="vmlinuz-acacia-lts"
KVERS="5.15.44"
BIN_DIR="bin"

def main():
    blog.initialize()

    if(not os.getuid() == 0):
        blog.error("Root permissions required to chroot to build environment.")
        return -1
    
    packages = ["base", "linux-lts", "coreutils", "procps-ng", "squashfs-tools", "leaf", "cpio","psmisc", "glibc", "gcc", "make", "bash", "sed", "grep", "gawk", "coreutils", "binutils", "findutils", "automake", "autoconf", "file", "gzip", "libtool", "m4", "groff", "patch", "texinfo", "which", "systemd", "python3", "networkmanager"]

    if(envmanager.setup(packages) != 0):
        return -1

    if(not os.path.exists(BIN_DIR)):
        blog.error("'bin' directory not found.")
        return -1
    
    if(initramfs.create_initramfs(envmanager.BUILD_ROOT_DIR, KNAME, KVERS, BIN_DIR) != 0):
        return -1
    
    if(squash.build_iso() != 0):
        return -1

if(__name__ == "__main__"):
    main()
