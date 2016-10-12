#!/usr/bin/env python2.7

import click
from marathon.marathon_pb2 import MarathonTask, ZKStoreEntry
import mesos.mesos_pb2 as Mesos
from kazoo.client import KazooClient
import logging
import sys
logging.basicConfig()


class ZooCleaner:
    def __init__(self, zkHostString, chroot, logLevel=logging.INFO):
        self.log = logging.getLogger(__name__)
        self.log.setLevel(logLevel)
        self.zkHostString = zkHostString
        self.chroot = chroot

        self.zk = KazooClient(hosts=zkHostString+chroot)
        self.zk.start()

    def query_yes_no(self, question, default="yes"):
        # From http://code.activestate.com/recipes/577058/
        valid = {"yes": True, "y": True, "ye": True,
                 "no": False, "n": False}
        if default is None:
            prompt = " [y/n] "
        elif default == "yes":
            prompt = " [Y/n] "
        elif default == "no":
            prompt = " [y/N] "
        else:
            raise ValueError("invalid default answer: '%s'" % default)

        while True:
            sys.stdout.write(question + prompt)
            choice = raw_input().lower()
            if default is not None and choice == '':
                return valid[default]
            elif choice in valid:
                return valid[choice]
            else:
                sys.stdout.write("Please respond with 'yes' or 'no' "
                                 "(or 'y' or 'n').\n")

    def clean(self):
        self.log.info("Looking for tasks on zk ensemble at: %s", self.zkHostString+self.chroot)

        marathon_state = self.zk.get_children('/state')
        lost_tasks = []
        for i in marathon_state:
            if 'task:' in i:
                self.log.debug("Retrieving task info for task: %s", i)
                task_bin = self.zk.get('/state/{}'.format(i))

                entry = ZKStoreEntry()
                entry.ParseFromString(task_bin[0])

                t = MarathonTask()
                t.ParseFromString(entry.value)
                if t.status.state == Mesos.TASK_LOST and t.status.reason == Mesos.TaskStatus.REASON_SLAVE_REMOVED:
                    self.log.warning("Found lost task: %s, host: %s", t.id, t.host)
                    lost_tasks.append(t)

        self.log.info("Total lost tasks: %d", len(lost_tasks))

        if len(lost_tasks) > 0:
            self.log.info("Begin prompt for delete lost tasks.")
            for task in lost_tasks:
                path = "/state/task:{}".format(task.id)

                if self.query_yes_no("Delete {}{}".format(self.chroot, path), "no"):
                    self.log.info("Deleting: {}".format(path))
                    self.zk.delete(path)
            self.log.info("Finished!")
            self.log.info("Be sure to `curl -X DELETE http://<marathon-host>:8080/v2/leader` to force election after deleting these tasks!")
        else:
            self.log.info("No lost tasks found. Finished!")


@click.command()
@click.option('--zk', envvar='ZOOKEEPER_URL', prompt='Zookeeper URL', help='Zookeeper host:port list')
@click.option('--chroot', envvar='ZOOKEEPER_CHROOT', prompt='Zookeeper Chroot', help='Zookeeper chroot path (default /marathon)', default='/marathon')
@click.option('--debug', is_flag=True, help='Enable debug logging')
def main(zk, chroot, debug):
    """
    Search a given Zookeeper Ensemble where Mesosphere's Marathon is running for tasks that have become zombies due to
    a slave being abruptly removed.

    Once the search is complete, ZooCleaner will prompt you (yes/no) if you'd like to delete the zombie tasks from
    Zookeeper. You will need to force a leader election in Marathon once this is complete to allow the fix to work.
    """

    if debug:
        logLevel = logging.DEBUG
    else:
        logLevel = logging.INFO

    cleaner = ZooCleaner(zk, chroot, logLevel)
    cleaner.clean()

if __name__ == "__main__":
    main()