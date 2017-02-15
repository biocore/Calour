# ----------------------------------------------------------------------------
# Copyright (c) 2016--, calour development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

from logging.config import fileConfig

from pkg_resources import resource_filename

from .experiment import Experiment, add_functions
from .io import read, read_taxa


__credits__ = "https://github.com/biocore/calour/graphs/contributors"
__version__ = "0.1.0.dev0"

__all__ = ['read', 'read_taxa', 'Experiment']

add_functions(Experiment)

log = resource_filename(__package__, 'log.cfg')

# setting False allows other logger to print log.
fileConfig(log, disable_existing_loggers=False)
