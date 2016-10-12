# marathon_zoocleaner
Find lost Marathon tasks and remove them from Zookeeper

## Warning!
This script was written to solve a particular problem I had with a Mesos host disappearing and Marathon showing 'ghost' tasks
in the WebUI (and refusing to scale applications because the number of running apps was satisfied by these ghosts).

I have not tested all edge cases where this script could potentially eat your ZK cluster.
It's fairly safe, but still, be sure you have a backup, or you're brave.

## Installation
`pip install -r requirements.txt` will install the basic requirements.

It's recommended to run this in a virtualenv, since the mesos protobuf files might conflict if you have 
mesos installed in site-packages on your host.

## Usage
```
./zoocleaner.py --help
Usage: zoocleaner.py [OPTIONS]

  Search a given Zookeeper Ensemble where Mesosphere's Marathon is running
  for tasks that have become zombies due to a slave being abruptly removed.

  Once the search is complete, ZooCleaner will prompt you (yes/no) if you'd
  like to delete the zombie tasks from Zookeeper. You will need to force a
  leader election in Marathon once this is complete to allow the fix to
  work.

Options:
  --zk TEXT      Zookeeper host:port list
  --chroot TEXT  Zookeeper chroot path (default /marathon)
  --debug        Enable debug logging
  --help         Show this message and exit.
  ```
 
## Bugs?
Yep, I'm sure there's a bug or two. Feel free to open an issue or a pull request :)
