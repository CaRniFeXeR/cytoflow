'''
Created on Dec 16, 2015

@author: brian
'''

from __future__ import division

from traits.api import HasStrictTraits, Str, CStr, File, Dict, Any, \
                       Instance, Tuple, Bool, Constant, Int, Float, List, \
                       Enum, provides, DelegatesTo, undefined
import numpy as np
import fcsparser
import warnings
import matplotlib.pyplot as plt
import math
from sklearn import mixture
from scipy import stats, linalg
import pandas as pd
import seaborn as sns
import matplotlib as mpl

from cytoflow.views.scatterplot import ScatterplotView

from cytoflow.operations import IOperation
from cytoflow.views import IView
from cytoflow.utility import CytoflowOpError, CytoflowViewError

@provides(IOperation)

class GaussianMixture2DOp(HasStrictTraits):
    """
    This module fits a Gaussian mixture model with a specified number of
    components to a pair of channels.
    
    Creates a new categorical metadata variable named `name`, with possible
    values `name_1` .... `name_n` where `n` is the number of components.
    An event is assigned to `name_i` category if it falls within `sigma`
    standard deviations of the component's mean.  If that is true for multiple
    categories (or if `sigma == 0.0`), the event is assigned to the category 
    with the highest posterior probability.  If the event doesn't fall into
    any category, it is assigned to `name_None`.
    
    Optionally, if `posteriors` is `True`, this module will also compute the 
    posterior probability of each event in each component.  Each component
    will have a metadata column named `name_i_Posterior` containing the
    posterior probability that that event is in that component.
    
    Finally, the same mixture model (mean and standard deviation) may not
    be appropriate for every subset of the data.  If this is the case, you
    can use the `by` attribute to specify metadata by which to aggregate
    the data before estimating (and applying) a mixture model.  The number of 
    components is the same across each subset, though.
    
    Attributes
    ----------
    name : Str
        The operation name; determines the name of the new metadata column
        
    xchannel : Str
        The X channel to apply the mixture model to.
        
    ychannel : Str
        The Y channel to apply the mixture model to.
        
    num_components : Int (default = 2)
        How many components to fit to the data?  Must be >= 2.

    sigma : Float (default = 0.0)
        How many standard deviations on either side of the mean to include
        in each category?  If an event is in multiple components, assign it
        to the component with the highest posterior probability.  If 
        `sigma == 0.0`, categorize *all* the data by assigning each event to
        the component with the highest posterior probability.  Must be >= 0.0.
    
    by : List(Str)
        A list of metadata attributes to aggregate the data before estimating
        the model.  For example, if the experiment has two pieces of metadata,
        `Time` and `Dox`, setting `by = ["Time", "Dox"]` will fit the model 
        separately to each subset of the data with a unique combination of
        `Time` and `Dox`.
        
    scale : Enum("linear", "log") (default = "linear")
        Re-scale the data before fitting the data?  
        TODO - not currently implemented.
        
    posteriors : Bool (default = False)
        If `True`, add one column per component giving the posterior probability
        that each event is in each component.  Useful for filtering out
        low-probability events.
    """
    
    id = Constant('edu.mit.synbio.cytoflow.operations.gaussian_2d')
    friendly_id = Constant("2D Gaussian Mixture")
    
    name = CStr()
    xchannel = Str()
    ychannel = Str()
    num_components = Int(2)
    sigma = Float(0.0)
    by = List(Str)
    
    # scale = Enum("linear", "log")
    
    posteriors = Bool(False)
    
    # the key is either a single value or a tuple
    _gmms = Dict(Any, Instance(mixture.GMM))
    
    def estimate(self, experiment, subset = None):
        """
        Estimate the Gaussian mixture model parameters
        """
        
        if not experiment:
            raise CytoflowOpError("No experiment specified")

        if self.xchannel not in experiment.data:
            raise CytoflowOpError("Column {0} not found in the experiment"
                                  .format(self.xchannel))
            
        if self.ychannel not in experiment.data:
            raise CytoflowOpError("Column {0} not found in the experiment"
                                  .format(self.ychannel))
            
        if self.num_components < 2:
            raise CytoflowOpError("num_components must be >= 2") 
       
        for b in self.by:
            if b not in experiment.data:
                raise CytoflowOpError("Aggregation metadata {0} not found"
                                      " in the experiment"
                                      .format(b))
            if len(experiment.data[b].unique()) > 100: #WARNING - magic number
                raise CytoflowOpError("More than 100 unique values found for"
                                      " aggregation metadata {0}.  Did you"
                                      " accidentally specify a data channel?"
                                      .format(b))
                
        if self.by:
            groupby = experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that contains
            # all the events
            groupby = experiment.data.groupby(lambda x: True)
            
        for group, data_subset in groupby:
            x = data_subset.loc[:, [self.xchannel, self.ychannel]].values
            gmm = mixture.GMM(n_components = self.num_components,
                              covariance_type = "full",
                              random_state = 1)
            gmm.fit(x)
            
            if not gmm.converged_:
                raise CytoflowOpError("Estimator didn't converge"
                                      " for group {0}"
                                      .format(group))
           
            self._gmms[group] = gmm
    
    def apply(self, experiment):
        """
        Assigns new metadata to events using the mixture model estimated
        in `estimate`.
        """
            
        if not experiment:
            raise CytoflowOpError("No experiment specified")
        
        # make sure name got set!
        if not self.name:
            raise CytoflowOpError("You have to set the gate's name "
                                  "before applying it!")

        if self.name in experiment.data.columns:
            raise CytoflowOpError("Experiment already has a column named {0}"
                                  .format(self.name))
        
        if not self._gmms:
            raise CytoflowOpError("No components found.  Did you forget to "
                                  "call estimate()?")

        if self.xchannel not in experiment.data:
            raise CytoflowOpError("Column {0} not found in the experiment"
                                  .format(self.xchannel))

        if self.ychannel not in experiment.data:
            raise CytoflowOpError("Column {0} not found in the experiment"
                                  .format(self.ychannel))
            
        if self.num_components < 2:
            raise CytoflowOpError("num_components must be >= 2") 
       
        for b in self.by:
            if b not in experiment.data:
                raise CytoflowOpError("Aggregation metadata {0} not found"
                                      " in the experiment"
                                      .format(b))

            if len(experiment.data[b].unique()) > 100: #WARNING - magic number
                raise CytoflowOpError("More than 100 unique values found for"
                                      " aggregation metadata {0}.  Did you"
                                      " accidentally specify a data channel?"
                                      .format(b))
                           
        if self.sigma < 0.0:
            raise CytoflowOpError("sigma must be >= 0.0")
        
        new_experiment = experiment.clone()
        name_dtype = np.dtype("S{0}".format(len(self.name) + 5))
        new_experiment.data[self.name] = \
            np.full(len(new_experiment.data.index), "", name_dtype)
        new_experiment.metadata[self.name] = {'type' : 'meta'}
        new_experiment.conditions[self.name] = "category"
        
        if self.posteriors:
            for i in range(0, self.num_components):
                col_name = "{0}_{1}_Posterior".format(self.name, i+1)
                new_experiment.data[col_name] = \
                    np.full(len(new_experiment.data.index), 0.0)
                new_experiment.metadata[col_name] = {'type' : 'meta'}
                new_experiment.conditions[col_name] = "float"
        
        # what we DON'T want to do is iterate through event-by-event.
        # the more of this we can push into numpy, sklearn and pandas,
        # the faster it's going to be.
        
        if self.by:
            groupby = new_experiment.data.groupby(self.by)
        else:
            # use a lambda expression to return a group that
            # contains all the events
            groupby = new_experiment.data.groupby(lambda x: True)
        
        for group, data_subset in groupby:
            gmm = self._gmms[group]
            x = data_subset.loc[:, [self.xchannel, self.ychannel]].values
            
            # make a preliminary assignment
            predicted = gmm.predict(x)
            
            # if we're doing sigma-based gating, for each component check
            # to see if the event is in the sigma gate.
            if self.sigma > 0.0:
                
                # make a quick dataframe with the value and the predicted
                # component
                gate_df = pd.DataFrame({"x" : x, "p" : predicted})

                # for each component, get the low and the high threshold
                for c in range(0, self.num_components):
                    lo = (gmm.means_[c][0] 
                          - self.sigma * np.sqrt(gmm.covars_[c][0]))
                    hi = (gmm.means_[c][0] 
                          + self.sigma * np.sqrt(gmm.covars_[c][0]))
                    
                    # and build an expression with numexpr so it evaluates fast!
                    gate_bool = gate_df.eval("p == @c and x >= @lo and x <= @hi").values
                    predicted[np.logical_and(predicted == c, gate_bool == False)] = -1
        
            # TODO - sort component assignments by mean.  eg, the lowest
            # mean should be component 1, then component 2, etc.
        
            cname = np.full(len(predicted), self.name + "_", name_dtype)
            predicted_str = np.char.mod('%d', predicted + 1) 
            predicted_str = np.char.add(cname, predicted_str)
            predicted_str[predicted == -1] = "{0}_None".format(self.name)

            # it took me a few goes to get this slicing right.  the key
            # is the use of .loc so you're not chaining lookups
            new_experiment.data.loc[groupby.groups[group], self.name] = \
                predicted_str
                    
            if self.posteriors:
                probability = gmm.predict_proba(x[:,np.newaxis])
                #print probability[:, 0]
                for i in range(0, self.num_components):
                    col_name = "{0}_{1}_Posterior".format(self.name, i+1)
                    #print probability[i]
                    new_experiment.data.loc[groupby.groups[group], col_name] = \
                        probability[:, i]
                    
        return new_experiment
    
    def default_view(self):
        """
        Returns a diagnostic plot of the Gaussian mixture model.
        
        Returns
        -------
            IView : an IView, call plot() to see the diagnostic plot.
        """
        return GaussianMixture2DView(op = self)
    
@provides(IView)
class GaussianMixture2DView(ScatterplotView):
    """
    Attributes
    ----------
    name : Str
        The instance name (for serialization, UI etc.)
        
    op : Instance(GaussianMixture2DOp)
        The op whose parameters we're viewing.
        
    group : Python (default: None)
        The subset of data to display.  Must match one of the keys of 
        `op._gmms`.  If `None` (the default), display a plot for each subset.
    """
    
    id = 'edu.mit.synbio.cytoflow.view.gaussianmixture2dview'
    friendly_id = "2D Gaussian Mixture Diagnostic Plot"
    
    # TODO - why can't I use GaussianMixture2DOp here?
    op = Instance(IOperation)
    name = DelegatesTo('op')
    xchannel = DelegatesTo('op')
    ychannel = DelegatesTo('op')
    huefacet = DelegatesTo('op', 'name')
    group = Any(None)
    
    def plot(self, experiment, **kwargs):
        """
        Plot the plots.
        """
        
        if not self.huefacet:
            raise CytoflowViewError("didn't set GaussianMixture2DOp.name")
        
        if not self.op._gmms:
            raise CytoflowViewError("Didn't find a model. Did you call "
                                    "estimate()?")
            
        if self.group and self.group not in self.op._gmms:
            raise CytoflowViewError("didn't find group {0} in op._gmms"
                                    .format(self.group))
        
        # if `group` wasn't specified, make a new plot per group.
        if self.op.by and not self.group:
            groupby = experiment.data.groupby(self.op.by)
            for group, _ in groupby:
                GaussianMixture2DView(op = self.op,
                                      group = group).plot(experiment, **kwargs)
                plt.title("{0} = {1}".format(self.op.by, group))
            return
                
        temp_experiment = experiment.clone()
        if self.group:
            groupby = experiment.data.groupby(self.op.by)
            temp_experiment.data = groupby.get_group(self.group)
        
        try:
            temp_experiment = self.op.apply(temp_experiment)
        except CytoflowOpError as e:
            raise CytoflowViewError(e.__str__())

        # plot the group's scatterplot, colored by component
        super(GaussianMixture2DView, self).plot(temp_experiment, **kwargs)
        
        # plot the actual distribution on top of it.  display as a "topo" 
        # plot with lines at 1, 2, and 3 standard deviations
        gmm = self.op._gmms[self.group] if self.group else self.op._gmms[True]
        for i, (mean, covar) in enumerate(zip(gmm.means_, gmm._get_covars())):
            v, w = linalg.eigh(covar)
            u = w[0] / linalg.norm(w[0])
            angle = np.arctan(u[1] / u[0])
            angle = 180 * angle / np.pi
            
            color_i = i % len(sns.color_palette())
            color = sns.color_palette()[color_i]
            ell = mpl.patches.Ellipse(mean, 
                                      np.sqrt(v[0]), 
                                      np.sqrt(v[1]),
                                      180 + angle, 
                                      color = color)
            ell.set_alpha(0.5)
            plt.gca().add_artist(ell)
    