#!/usr/bin/env python2.7

# (c) Massachusetts Institute of Technology 2015-2016
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

'''
Created on Sep 13, 2016

@author: brian
'''

from __future__ import division, absolute_import

from warnings import warn

from traits.api import (HasStrictTraits, Str, List, Constant, provides, 
                        Callable, CStr)

import cytoflow.utility as util

from .i_operation import IOperation

@provides(IOperation)
class Statistics1DOp(HasStrictTraits):
    """
    Apply a function to subsets of a data set, and add it as a statistic
    to the experiment.
    
    The `apply()` function groups the data by the variables in `by`, then
    applies the `function` callable to each subset.  The callable should take
    a Series and return a float.
    
    Attributes
    ----------
    name : Str
        The operation name.  Becomes the first element in the
        Experiment.statistics key tuple.
    
    channel : Str
        The channel to apply the function to.
        
    function : Callable
        The function used to compute the statistic.  `function` must take a 
        Series and returns a float.  If `statistic_name` is empty, the name of 
        the function becomes the second in element in the Experiment.statistics 
        key tuple.
        
    statistic_name : Str
        The name of the function; if present, becomes the second element in
        the Experiment.statistics key tuple.
        
    by : List(Str)
        A list of metadata attributes to aggregate the data before applying the
        function.  For example, if the experiment has two pieces of metadata,
        `Time` and `Dox`, setting `by = ["Time", "Dox"]` will apply `function` 
        separately to each subset of the data with a unique combination of
        `Time` and `Dox`.
        
    subset : Str
        A Python expression sent to Experiment.query() to subset the data before
        computing the statistic.
   
    Examples
    --------
    
    >>> stats_op = Statistics1DOp(name = "Mean",
    ...                           channel = "Y2-A",
    ...                           function = np.mean,
    ...                           by = ["Dox"])
    >>> ex2 = stats_op.apply(ex)
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.statistics')
    friendly_id = Constant("Statistics")
    
    name = CStr()
    channel = Str()
    function = Callable()
    statistic_name = Str()
    by = List(Str)
    subset = Str()
    
    def apply(self, experiment):
        """
        Estimate the Gaussian mixture model parameters
        """
        
        if not experiment:
            raise util.CytoflowOpError("Must specify an experiment")

        if not self.name:
            raise util.CytoflowOpError("Must specify a name")
        
        if not self.channel:
            raise util.CytoflowOpError("Must specify a channel")

        if not self.function:
            raise util.CytoflowOpError("Must specify a function")

        if self.channel not in experiment.data:
            raise util.CytoflowOpError("Channel {0} not found in the experiment"
                                  .format(self.channel))
            
        if not self.by:
            raise util.CytoflowOpError("Must specify some grouping conditions "
                                       "in 'by'")
       
        for b in self.by:
            if b not in experiment.data:
                raise util.CytoflowOpError("Aggregation metadata {0} not found"
                                      " in the experiment"
                                      .format(b))
            if len(experiment.data[b].unique()) > 100: #WARNING - magic number
                raise util.CytoflowOpError("More than 100 unique values found for"
                                      " aggregation metadata {0}.  Did you"
                                      " accidentally specify a data channel?"
                                      .format(b))
                
        if self.subset:
            try:
                experiment = experiment.query(self.subset)
            except:
                raise util.CytoflowOpError("Subset string '{0}' isn't valid"
                                        .format(self.subset))
                
            if len(experiment) == 0:
                raise util.CytoflowOpError("Subset string '{0}' returned no events"
                                        .format(self.subset))
                
        groupby = experiment.data.groupby(self.by)

        for group, data_subset in groupby:
            if len(data_subset) == 0:
                warn("Group {} had no data"
                     .format(group), 
                     util.CytoflowOpWarning)
        
        try:
            stat = groupby[self.channel].aggregate(self.function)
        except Exception as e:
            raise util.CytoflowOpError("Your function threw an error: {}"
                                  .format(e))
        
        new_experiment = experiment.clone()
        new_experiment.history.append(self.clone_traits(transient = lambda t: True))
        if self.statistic_name:
            new_experiment.statistics[(self.name, self.statistic_name)] = stat
        else:
            new_experiment.statistics[(self.name, self.function.__name__)] = stat

        
        return new_experiment
