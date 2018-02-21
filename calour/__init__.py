# ----------------------------------------------------------------------------
# Copyright (c) 2016--, calour development team.
#
# Distributed under the terms of the Modified BSD License.
#
# The full license is in the file COPYING.txt, distributed with this software.
# ----------------------------------------------------------------------------

import inspect
from logging.config import fileConfig

from pkg_resources import resource_filename

from .experiment import Experiment
from .amplicon_experiment import AmpliconExperiment
from .io import read, read_amplicon, read_open_ms
from .util import set_log_level, _convert_axis_name, register_functions


__credits__ = "https://github.com/biocore/calour/graphs/contributors"
__version__ = "1.0-dev"

__all__ = ['read', 'read_amplicon', 'read_open_ms',
           'Experiment', 'AmpliconExperiment',
           'set_log_level']

# add member functions to the class
register_functions(Experiment)
register_functions(AmpliconExperiment)

# decorate all the class functions to convert axis
for fn, f in inspect.getmembers(Experiment, predicate=inspect.isfunction):
    setattr(Experiment, fn, _convert_axis_name(f))

log = resource_filename(__package__, 'log.cfg')

# setting False allows other logger to print log.
fileConfig(log, disable_existing_loggers=False)
