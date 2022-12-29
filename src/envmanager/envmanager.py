import os

from pyleaf import pyleafcore
from log import blog

BUILD_ROOT_DIR = "./buildroot"
ROOT_PW = "acacia"

def setup(packages):
    leafcore_instance = None
    try:
        leafcore_instance = pyleafcore.Leafcore()
    except Exception:
        blog.error("Could not setup leafcore.")
        return -1
    
    leafcore_instance.setVerbosity(2)

    if(not os.path.exists(BUILD_ROOT_DIR)):
        blog.info("Creating build environment..")
        os.mkdir(BUILD_ROOT_DIR)
    
    # set root dir
    leafcore_instance.setRootDir(BUILD_ROOT_DIR)
    
    # leafcore options
    leafcore_instance.setBoolConfig(pyleafcore.LeafConfig_bool.CONFIG_NOASK, True)
    leafcore_instance.setBoolConfig(pyleafcore.LeafConfig_bool.CONFIG_FORCEOVERWRITE, True)
    leafcore_instance.setBoolConfig(pyleafcore.LeafConfig_bool.CONFIG_RUNPOSTINSTALL, False)
    leafcore_instance.setBoolConfig(pyleafcore.LeafConfig_bool.CONFIG_NOPROGRESS, True)

    # update pkglist
    leafcore_instance.a_update()

    # setup buildroot
    if(leafcore_instance.a_install(packages) != 0):
        blog.error("Failed to deploy packages.")
        return -1

    # run upgrade..
    if(leafcore_instance.a_upgrade([]) != 0):
        blog.error("Failed to upgrade packages.")
        return -1

    # fixing up shadow
    blog.info("Running pwconv..")
    os.system("chroot {} /usr/sbin/pwconv".format(BUILD_ROOT_DIR))

    blog.info("Running pwconv..")
    os.system("chroot {} /usr/sbin/grpconv".format(BUILD_ROOT_DIR))

    blog.info("Setting root passwd..")
    cmd = "/usr/bin/echo \"root:{}\" | /usr/sbin/chpasswd".format(ROOT_PW)
    os.system("chroot {} /usr/bin/sh -c \"{}\"".format(BUILD_ROOT_DIR, cmd))
    return 0
