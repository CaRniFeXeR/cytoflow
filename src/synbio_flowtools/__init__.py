# make sure pandas is new enough
from pandas.version import version as _pd_version
from distutils.version import LooseVersion

if LooseVersion(_pd_version) < '0.15.0':
    raise ImportError('synbio_flowtools needs pandas >= 0.15.0.  trust me.')

# make sure numexpr is around.

from numexpr import version as _numexpr_version

if LooseVersion(_numexpr_version.version) < '2.1':
    raise ImportError('synbio_flowtools needs numexpr >= 2.1')

from experiment import Experiment
from operations.threshold import ThresholdOp
