"""Sub-commands factory."""
from bcbiovm.client.subcommands import cluster
from bcbiovm.client.subcommands import config
from bcbiovm.client.subcommands import docker
from bcbiovm.client.subcommands import icel

# TODO(alexandrucoman): Add support for dynamically loading subcommands

_SUBCOMMANDS = {
    'cluster': {
        'Bootstrap': cluster.Bootstrap,
        'Command': cluster.Command,
        'Setup': cluster.Setup,
        'Start': cluster.Start,
        'Stop': cluster.Stop,
        'SSHConnection': cluster.SSHConnection,
    },
    'config': {
        'Edit': config.Edit,
    },
    'docker': {
        'Build': docker.Build,
        'BiodataUpload': docker.BiodataUpload,
        'SystemUpdate': docker.SystemUpdate,
        'SetupInstall': docker.SetupInstall,
        'RunFunction': docker.RunFunction,
    },
    'icel': {
        'Create': icel.Create,
        'Mount': icel.Mount,
        'Unmount': icel.Unmount,
        'Stop': icel.Stop,
        'Specification': icel.Specification
    }
}


def get(container, name):
    """Return the required subcommand."""
    # TODO(alexandrucoman): Check the received information
    return _SUBCOMMANDS[container][name]
