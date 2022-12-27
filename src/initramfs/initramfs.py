import os
import shutil
import subprocess

from log import blog

WORK_DIRECTORY = "initramfsbuild"

BASE_FS = [ "dev", "run", "sys", "proc", "usr", "etc" ]
USR_SUB = [ "bin", "lib", "sbin" ]
USR_LIB_SUB = [ "firmware", "modules" ]
ETC_SUB = [ "modprobe.d", "udev" ]

# udevd -> /usr/lib/systemd-udevd
BINFILES = ["sh", "cat", "cp", "dd", "killall", "ls", "mkdir", "mknod", "mount", "fgrep", "find", "egrep", "sed", "xargs", "grep", "umount", "sed", "sleep", "ln", "rm", "uname", "readlink", "basename", "udevadm", "kmod"]
SBINFILES = ["blkid", "switch_root"]

def touch_file(file):
    with open(file, "w", encoding="utf-8") as f:
        pass

def copy_with_deps(buildroot, binfile, deps_list):
    blog.info("Copying binary {} with dependencies..".format(binfile))
    
    binpath = os.path.relpath(binfile, start="buildroot")
    shutil.copy(os.path.join("buildroot", binpath), os.path.join(WORK_DIRECTORY, binpath))

    for dep in deps_list:
        blog.info("Copying library {}..".format(dep))
        shutil.copy(os.path.join(buildroot, dep[1:len(dep)]), os.path.join(WORK_DIRECTORY, dep[1:len(dep)]))

# uses ldd to get all dependencies of a given dynamic binary
def get_dependencies(binfile):
    if(not os.path.exists(binfile)):
        return [ ]

    proc = subprocess.run(["ldd", binfile], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    deps = proc.stdout.split("\n")

    libs = [ ]

    for d in deps:
        # skip pseudo libraries and libsystemd
        if("linux-vdso.so.1" in d or "linux-gate.so.1" in d or "libsystemd-shared" in d):
            continue
        
        split = d.strip().split("=>") 
        if(len(split) == 2):
            dep_str = split[1].strip().split(" ")[0].strip()
            libs.append(dep_str)
    
    return libs

def create_initramfs(buildroot, kname, kver, bindir):
    kmod_dir = os.path.join(buildroot, "usr/lib/modules/{}".format(kver))

    if(not os.path.exists(kmod_dir)):
        blog.error("No kernel modules directory found for given kernel version.")
        return -1

    blog.info("Creating temporary initramfs build directory..")
    
    # probaly CTRL+C, clean up..
    if(os.path.exists(WORK_DIRECTORY)):
        blog.warn("Removing old work directory..")
        shutil.rmtree(WORK_DIRECTORY)

    os.mkdir(WORK_DIRECTORY)
    
    # base directory structure
    for path in BASE_FS:
        target = os.path.join(WORK_DIRECTORY, path)
        blog.info("Creating {}".format(target))
        os.mkdir(target)
    
    usr_path = os.path.join(WORK_DIRECTORY, "usr")
    for path in USR_SUB:
        target = os.path.join(usr_path, path)
        blog.info("Creating {}".format(target))
        os.mkdir(target)
    
    lib_path = os.path.join(usr_path, "lib")
    for path in USR_LIB_SUB:
        target = os.path.join(usr_path, path)
        blog.info("Creating {}".format(target))
        os.mkdir(target)
   
    etc_path = os.path.join(WORK_DIRECTORY, "etc")
    for path in ETC_SUB:
        target = os.path.join(etc_path, path)
        blog.info("Creating {}".format(target))
        os.mkdir(target)

    # symlinks
    blog.info("Creating symlinks..")
    os.symlink("/usr/bin", os.path.join(WORK_DIRECTORY, "bin"))
    os.symlink("/usr/lib", os.path.join(WORK_DIRECTORY, "lib"))
    os.symlink("/usr/sbin", os.path.join(WORK_DIRECTORY, "sbin"))
    os.symlink("/lib", os.path.join(WORK_DIRECTORY, "lib64"))
    
    # mk null and console
    blog.info("Creating device nodes..")
    os.system("mknod -m 640 {} c 5 1".format(os.path.join(WORK_DIRECTORY, "dev/console")))
    os.system("mknod -m 664 {} c 5 1".format(os.path.join(WORK_DIRECTORY, "dev/null")))
    
    blog.info("Copying udev configuration..")
    try:
        # copy udev.conf from buildroot
        shutil.copy(os.path.join(buildroot, "etc/udev/udev.conf"), os.path.join(WORK_DIRECTORY, "etc/udev/udev.conf"))
        # rules.d
        shutil.copytree(os.path.join(buildroot, "etc/udev/rules.d"), os.path.join(WORK_DIRECTORY, "etc/udev/rules.d"))
    except FileNotFoundError as ex:
        blog.error("Could not find required udev configuration files: {}".format(ex))
        return -1

    # copy firmware, if it exists..
    if(os.path.exists(os.path.join(buildroot, "usr/lib/firmware"))):
        blog.info("Copying linux-firmware..")
        shutil.copytree(os.path.join(buildroot, "usr/lib/firmware"), os.path.join(WORK_DIRECTORY, "usr/lib/firmware"))
    
    if(not os.path.exists(os.path.join(bindir, "init"))):
       blog.error("No init binary available.")
       return -1
    
    blog.info("Copying init binary..")
    shutil.copy(os.path.join(bindir, "init"), os.path.join(WORK_DIRECTORY, "init"))
    
    blog.info("Copying /usr/bin binaries..")
    for b in BINFILES:
        b_path = os.path.join(buildroot, os.path.join("usr/bin", b))
        copy_with_deps(buildroot, b_path, get_dependencies(b_path))

    blog.info("Copying /usr/sbin binaries..")
    for b in SBINFILES:
        b_path = os.path.join(buildroot, os.path.join("usr/sbin", b))
        copy_with_deps(buildroot, b_path, get_dependencies(b_path))

    blog.info("Copying systemd-udevd..")
    sd_udevd = "usr/lib/systemd/systemd-udevd"

    sd_udevd_path = os.path.join(buildroot, sd_udevd)
    sd_udevd_deps = get_dependencies(sd_udevd_path)
    
    for dep in sd_udevd_deps:
        blog.info("Copying library {}..".format(dep))
        shutil.copy(os.path.join(buildroot, dep[1:len(dep)]), os.path.join(WORK_DIRECTORY, dep[1:len(dep)]))

    shutil.copy(sd_udevd, os.path.join(WORK_DIRECTORY, sd_udevd))
    
    blog.info("Symlinking /usr/bin/kmod..")
    os.symlink("/usr/bin/kmod", os.path.join(WORK_DIRECTORY, "lsmod"))
    os.symlink("/usr/bin/kmod", os.path.join(WORK_DIRECTORY, "insmod"))
    
    blog.info("Copying udev, systemd and elogin config files")
    shutil.copytree(os.path.join(buildroot, "usr/lib/udev"), os.path.join(WORK_DIRECTORY, "usr/lib/udev"))
    shutil.copytree(os.path.join(buildroot, "usr/lib/systemd"), os.path.join(WORK_DIRECTORY, "usr/lib/systemd"))
    shutil.copytree(os.path.join(buildroot, "usr/lib/elogin"), os.path.join(WORK_DIRECTORY, "usr/lib/elogin"))
    
    blog.info("Copying kernel modules...")
    shutil.copytree(kmod_dir, os.path.join(WORK_DIRECTORY, "usr/lib/modules/{}".format(kver)))

    blog.info("Running depmod..")
    os.system("depmod -b {} {}".format(WORK_DIRECTORY, kver))

    blog.info("Compressing initrd..")
    initrd_file = "acacia-initrd.img"
    os.system("(cd {}; find . | cpio -o -H newc --quiet | gzip -9) > {}".format(WORK_DIRECTORY, initrd_file))

    shutil.copy(os.path.join(WORK_DIRECTORY, initrd_file), initrd_file)
    blog.info("Created initramfs.")


