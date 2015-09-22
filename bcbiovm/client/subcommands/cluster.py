"""Run and manage a cluster using elasticluster."""
from __future__ import print_function

import abc
import argparse

from bcbiovm.client import base
from bcbiovm.common import constant
from bcbiovm.common import objects
from bcbiovm.common import utils
from bcbiovm.provider import factory as cloud_factory

LOG = utils.get_logger(__name__)


class CommandMixin(base.Command):

    """Base command class for commands which are ussing AnsiblePlaybook."""

    @staticmethod
    def _process_playbook_response(response):
        """Process the information received from AnsiblePlaybook."""
        status = True
        report = objects.Report()
        fields = [
            {"name": "playbook", "title": "Ansible playbook"},
            {"name": "unreachable", "title": "Unreachable host"},
            {"name": "failures", "title": "Hosts where playbook failed."}
        ]

        for playbook, playbook_info in response.items():
            if not playbook_info.status:
                status = False

            section = report.add_section(
                name=playbook, fields=fields,
                title="Ansible playbook: %s" % playbook)
            section.add_item([playbook, playbook_info.unreachable,
                              playbook_info.failures])

        return(status, report)

    @abc.abstractmethod
    def setup(self):
        """Extend the parser configuration in order to expose this command."""
        pass

    @abc.abstractmethod
    def work(self):
        """Override this with your desired procedures."""
        pass


class Bootstrap(CommandMixin):

    """Update a bcbio AWS system with the latest code and tools."""

    def setup(self):
        parser = self._parser.add_parser(
            "bootstrap",
            help="Update a bcbio AWS system with the latest code and tools",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
            "--econfig", default=None,
            help="Elasticluster bcbio configuration file")
        parser.add_argument(
            "-c", "--cluster", default="bcbio",
            help="elasticluster cluster name")
        parser.add_argument(
            "-R", "--no-reboot", default=False, action="store_true",
            help="Don't upgrade the cluster host OS and reboot")
        parser.set_defaults(work=self.run)

    def work(self):
        """Run the command with the received information."""
        if self.args.econfig is None:
            self.args.econfig = constant.PATH.EC_CONFIG.format(
                provider=self.args.provider)

        provider = cloud_factory.get(self.args.provider)()
        response = provider.bootstrap(cluster=self.args.cluster,
                                      config=self.args.econfig,
                                      reboot=not self.args.no_reboot)
        status, report = self._process_playbook_response(response)
        if status:
            LOG.debug("All playbooks runned without problems.")
        else:
            LOG.error("Something went wrong.")
            print(report.text())


class Command(base.Command):

    """Run a script on the bcbio frontend node inside a screen session."""

    def setup(self):
        """Extend the parser configuration in order to expose this command."""
        parser = self._parser.add_parser(
            "command",
            help="Run a script on the bcbio frontend "
                 "node inside a screen session",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
            "--econfig", default=None,
            help="Elasticluster bcbio configuration file")
        parser.add_argument(
            "-c", "--cluster", default="bcbio",
            help="elasticluster cluster name")
        parser.add_argument(
            "script", metavar="SCRIPT",
            help="Local path of the script to run. The screen "
                 "session name is the basename of the script.")
        parser.set_defaults(work=self.run)

    def work(self):
        """Run the command with the received information."""
        if self.args.econfig is None:
            self.args.econfig = constant.PATH.EC_CONFIG.format(
                provider=self.args.provider)
        provider = cloud_factory.get(self.args.provider)()
        return provider.run_script(cluster=self.args.cluster,
                                   config=self.args.econfig,
                                   script=self.args.script)


class Setup(base.Command):

    """Rerun cluster configuration steps."""

    def setup(self):
        """Extend the parser configuration in order to expose this command."""
        parser = self._parser.add_parser(
            "setup", help="Rerun cluster configuration steps",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
            "--econfig", default=None,
            help="Elasticluster bcbio configuration file")
        parser.add_argument(
            "-c", "--cluster", default="bcbio",
            help="elasticluster cluster name")
        parser.set_defaults(work=self.run)

    def work(self):
        """Run the command with the received information."""
        if self.args.econfig is None:
            self.args.econfig = constant.PATH.EC_CONFIG.format(
                provider=self.args.provider)
        provider = cloud_factory.get(self.args.provider)()
        return provider.setup(cluster=self.args.cluster,
                              config=self.args.econfig)


class Start(CommandMixin):

    """Start a bcbio cluster."""

    def setup(self):
        """Extend the parser configuration in order to expose this command."""
        parser = self._parser.add_parser(
            "start", help="Start a bcbio cluster",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
            "--econfig", default=None,
            help="Elasticluster bcbio configuration file")
        parser.add_argument(
            "-c", "--cluster", default="bcbio",
            help="elasticluster cluster name")
        parser.add_argument(
            "-R", "--no-reboot", default=False, action="store_true",
            help="Don't upgrade the cluster host OS and reboot")
        parser.set_defaults(work=self.run)

    def work(self):
        """Run the command with the received information."""
        if self.args.econfig is None:
            self.args.econfig = constant.PATH.EC_CONFIG.format(
                provider=self.args.provider)
        provider = cloud_factory.get(self.args.provider)()
        status = provider.start(cluster=self.args.cluster,
                                config=self.args.econfig,
                                no_setup=False)

        if status != 0:
            LOG.error("Failed to create the cluster.")
            return

        # Run bootstrap only if the start command successfully runned.
        response = provider.bootstrap(cluster=self.args.cluster,
                                      config=self.args.econfig,
                                      reboot=not self.args.no_reboot)

        status, report = self._process_playbook_response(response)
        if status:
            LOG.debug("All playbooks runned without problems.")
        else:
            LOG.error("Something went wrong.")
            print(report.text())


class Stop(base.Command):

    """Stop a bcbio cluster."""

    def setup(self):
        """Extend the parser configuration in order to expose this command."""
        parser = self._parser.add_parser(
            "stop", help="Stop a bcbio cluster",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
            "--econfig", default=None,
            help="Elasticluster bcbio configuration file")
        parser.add_argument(
            "-c", "--cluster", default="bcbio",
            help="elasticluster cluster name")
        parser.set_defaults(work=self.run)

    def work(self):
        """Run the command with the received information."""
        if self.args.econfig is None:
            self.args.econfig = constant.PATH.EC_CONFIG.format(
                provider=self.args.provider)
        provider = cloud_factory.get(self.args.provider)()
        return provider.stop(cluster=self.args.cluster,
                             config=self.args.econfig,
                             force=False,
                             use_default=False)


class SSHConnection(base.Command):

    """SSH to a bcbio cluster."""

    def setup(self):
        """Extend the parser configuration in order to expose this command."""
        parser = self._parser.add_parser(
            "ssh", help="SSH to a bcbio cluster",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        parser.add_argument(
            "--econfig", default=None,
            help="Elasticluster bcbio configuration file")
        parser.add_argument(
            "-c", "--cluster", default="bcbio",
            help="elasticluster cluster name")
        parser.add_argument(
            "args", metavar="ARG", nargs="*",
            help="Execute the following command on the remote "
                 "machine instead of opening an interactive shell.")
        parser.set_defaults(work=self.run)

    def work(self):
        """Run the command with the received information."""
        if self.args.econfig is None:
            self.args.econfig = constant.PATH.EC_CONFIG.format(
                provider=self.args.provider)
        provider = cloud_factory.get(self.args.provider)()
        return provider.ssh(cluster=self.args.cluster,
                            config=self.args.econfig,
                            ssh_args=self.args.args)
