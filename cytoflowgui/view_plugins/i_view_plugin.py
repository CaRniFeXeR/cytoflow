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

"""
Created on Mar 15, 2015

@author: brian
"""

from traits.api import (Interface, Str, HasTraits, Instance, on_trait_change, 
                        Dict, List, Property)
from traitsui.api import Handler

import cytoflow.utility as util
from cytoflowgui.util import DelayedEvent

VIEW_PLUGIN_EXT = 'edu.mit.synbio.cytoflow.view_plugins'

class IViewPlugin(Interface):
    """
    
    Attributes
    ----------
    
    id : Str
        The envisage ID used to refer to this plugin
        
    view_id : Str
        Same as the "id" attribute of the IView this plugin wraps
        Prefix: edu.mit.synbio.cytoflowgui.view
        
    short_name : Str
        The view's "short" name - for menus, toolbar tips, etc.
    """
    
    view_id = Str
    short_name = Str

    def get_view(self):
        """Return an IView instance that this plugin wraps"""
        
    
    def get_icon(self):
        """
        Returns an icon for this plugin
        """
        
class PluginViewMixin(HasTraits):
    handler = Instance(Handler, transient = True)    
    changed = DelayedEvent(delay = 0.1)
    
    subset_dict = Dict(Str, List, estimate = True)
    subset = Property(Str, depends_on = "subset_dict")
        
    def _get_subset(self):
        ret = []
        for key, values in self.subset_dict.iteritems():
            if values:
                values = list(values)
                values = ['"{}"'.format(x) if isinstance(x, basestring) else x for x in values]
                values = ["{} == {}".format(key, x) for x in values]
                values = " or ".join(values)
                ret.append(values)
        
        ret = ["({})".format(x) for x in ret]
        ret = " and ".join(ret)
        
        return ret
    
    # why can't we just put this in a workflow listener?  it's because
    # we sometimes need to override or supplement it on a per-module basis
        
    @on_trait_change("+", post_init = True)
    def _changed(self, obj, name, old, new):
        if not obj.trait(name).transient:
            if obj.trait(name).status:
                self.changed = "status"
            else:
                self.changed = "api"
            
    def should_plot(self, changed):
        """
        Should the owning WorkflowItem refresh the plot when certain things
        change?  `changed` can be:
         - "view" -- the view's parameters changed
         - "result" -- this WorkflowItem's result changed
         - "prev_result" -- the previous WorkflowItem's result changed
         - "estimate_result" -- the results of calling "estimate" changed
        """
        return True
    
    def plot_wi(self, wi):
        self.plot(wi.result, wi.current_plot)
            
    def enum_plots_wi(self, wi):
        try:
            return self.enum_plots(wi.result)
        except:
            return []
            

class ViewHandlerMixin(HasTraits):
    statistics = Property(depends_on = "info.ui.context")
    
    def _get_statistics(self):
        context = self.info.ui.context['context']
        if context:
            return context.statistics.keys()
        else:
            return []
        
    conditions = Property(depends_on = "info.ui.context")
    previous_conditions = Property(depends_on = "info.ui.context")
    
    def _get_conditions(self):
        context = self.info.ui.context['context']
        if context:
            return context.conditions.keys()
        else:
            return []

    def _get_previous_conditions(self):
        context = self.info.ui.context['context']
        if context and context.previous:
            return context.previous.conditions.keys()
        else:
            return []