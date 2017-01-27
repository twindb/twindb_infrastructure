import shlex
import subprocess
import time
from twindb_infrastructure import log


def run_command(command):
    log.debug("Executing: %r" % command)
    try:
        process = subprocess.Popen(shlex.split(command),
                                   stdout=subprocess.PIPE)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                log.info(output)
        rc = process.poll()
        log.debug("Exit code: %d" % rc)
        if rc != 0:
            raise subprocess.CalledProcessError(rc, command)
        return rc
    except (OSError, ValueError) as err:
        log.error(err)
        return -1


def disable_selinux(ip, username, key):

    try:
        cmd_common = ["ssh", "-t",
                      "-o", "StrictHostKeyChecking=no",
                      "-i", key,
                      "-l", username,
                      ip,
                      "sudo"]
        cmd = cmd_common + ["sed", "-i",
                            "s/SELINUX=enforcing/SELINUX=disabled/",
                            "/etc/selinux/config", "/etc/sysconfig/selinux"]
        log.debug("Executing: %r" % cmd)
        subprocess.check_output(cmd, stderr=subprocess.STDOUT)

        try:
            cmd = cmd_common + ["reboot"]
            log.debug("Executing: %r" % cmd)
            subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError:
            pass

        if not wait_sshd(ip, key, username):
            return False
        return True

    except subprocess.CalledProcessError as err:
        log.error(err.output)
        return False


def wait_sshd(ip, key_file, username):
    # Wait will sshd is up
    timeout = 300
    log.info("Waiting till sshd on %s starts" % ip)
    while subprocess.call(["ssh", "-o", "StrictHostKeyChecking=no",
                           "-o", "PasswordAuthentication=no",
                           "-i", key_file, "-l", username, ip,
                           "ls"]) != 0:
        log.info("Waiting %d more seconds" % timeout)
        time.sleep(3)
        timeout -= 3
        if timeout == 0:
            log.error("Failed to start sshd. Timeout expired")
            return False
    return True
