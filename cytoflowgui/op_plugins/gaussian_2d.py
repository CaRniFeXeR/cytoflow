#!/usr/bin/env python3.4
# coding: latin-1

# (c) Massachusetts Institute of Technology 2015-2017
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
Created on Oct 9, 2015

@author: brian
'''

from sklearn import mixture

from traitsui.api import View, Item, EnumEditor, Controller, VGroup, TextEditor, \
                         CheckListEditor, ButtonEditor
from envisage.api import Plugin, contributes_to
from traits.api import (provides, Callable, List, Str, Dict, Any, Instance,
                        DelegatesTo, Property, on_trait_change)
from pyface.api import ImageResource

import cytoflow.utility as util

from cytoflow.operations import IOperation
from cytoflow.operations.gaussian import GaussianMixtureOp, GaussianMixture2DView
from cytoflow.views.i_selectionview import IView

from cytoflowgui.view_plugins.i_view_plugin import ViewHandlerMixin, PluginViewMixin
from cytoflowgui.op_plugins import IOperationPlugin, OpHandlerMixin, OP_PLUGIN_EXT, shared_op_traits
from cytoflowgui.subset import ISubset, SubsetListEditor
from cytoflowgui.color_text_editor import ColorTextEditor
from cytoflowgui.op_plugins.i_op_plugin import PluginOpMixin, PluginHelpMixin
from cytoflowgui.workflow import Changed

class GaussianMixture2DHandler(OpHandlerMixin, Controller):
    def default_traits_view(self):
        return View(Item('name',
                         editor = TextEditor(auto_set = False)),
                    Item('xchannel',
                         editor=EnumEditor(name='context.previous_wi.channels'),
                         label = "X Channel"),
                    Item('ychannel',
                         editor=EnumEditor(name='context.previous_wi.channels'),
                         label = "Y Channel"),
                    Item('x_channel_scale',
                         label = "X Scale"),
                    Item('y_channel_scale',
                         label = "Y Scale"),
                    VGroup(
                    Item('num_components', 
                         editor = TextEditor(auto_set = False),
                         label = "Num\nComponents"),
                    Item('sigma',
                         editor = TextEditor(auto_set = False)),
                    Item('by',
                         editor = CheckListEditor(cols = 2,
                                                  name = 'handler.previous_conditions_names'),
                         label = 'Group\nEstimates\nBy',
                         style = 'custom'),
                    VGroup(Item('subset_list',
                                show_label = False,
                                editor = SubsetListEditor(conditions = "context.previous_wi.conditions")),
                           label = "Subset",
                           show_border = False,
                           show_labels = False),
                    Item('do_estimate',
                         editor = ButtonEditor(value = True,
                                               label = "Estimate!"),
                         show_label = False),
                    label = "Estimation parameters",
                    show_border = False),
                    shared_op_traits)

class GaussianMixture2DPluginOp(PluginOpMixin, GaussianMixtureOp):
    handler_factory = Callable(GaussianMixture2DHandler)
    
    xchannel = Str
    ychannel = Str
    x_channel_scale = util.ScaleEnum(estimate = True)
    y_channel_scale = util.ScaleEnum(estimate = True)
    
    # add "estimate" metadata
    num_components = util.PositiveInt(1, estimate = True)
    sigma = util.PositiveFloat(0.0, allow_zero = True, estimate = True)
    by = List(Str, estimate = True)
    xscale = util.ScaleEnum(estimate = True)
    yscale = util.ScaleEnum(estimate = True)
    
    _gmms = Dict(Any, Instance(mixture.GaussianMixture), transient = True)
    
    # bits to support the subset editor
    
    subset_list = List(ISubset, estimate = True)    
    subset = Property(Str, depends_on = "subset_list.str")
        
    # MAGIC - returns the value of the "subset" Property, above
    def _get_subset(self):
        return " and ".join([subset.str for subset in self.subset_list if subset.str])
    
    @on_trait_change('subset_list.str', post_init = True)
    def _subset_changed(self, obj, name, old, new):
        self.changed = (Changed.ESTIMATE, ('subset_list', self.subset_list))
        

    @on_trait_change('xchannel, ychannel')
    def _channel_changed(self):
        self.channels = [self.xchannel, self.ychannel]
        self.changed = (Changed.ESTIMATE, ('channels', self.channels))
        
    @on_trait_change('x_channel_scale, y_channel_scale')
    def _scale_changed(self):
        if self.xchannel:
            self.scale[self.xchannel] = self.x_channel_scale
            
        if self.ychannel:
            self.scale[self.ychannel] = self.y_channel_scale
            
        self.changed = (Changed.ESTIMATE, ('scale', self.scale))

    def default_view(self, **kwargs):
        return GaussianMixture2DPluginView(op = self, **kwargs)
    
    def estimate(self, experiment):
        super().estimate(experiment, subset = self.subset)
        self.changed = (Changed.ESTIMATE_RESULT, self)
    
    def clear_estimate(self):
        self._gmms.clear()
        self._scale = {}
        self.changed = (Changed.ESTIMATE_RESULT, self)
        
    def should_clear_estimate(self, changed):
        if changed == Changed.ESTIMATE:
            return True
        
        return False

class GaussianMixture2DViewHandler(ViewHandlerMixin, Controller):
    def default_traits_view(self):
        return View(VGroup(
                    VGroup(Item('xchannel',
                                style = 'readonly'),
                           Item('ychannel',
                                style = 'readonly'),
                           label = "2D Mixture Model Default Plot",
                           show_border = False)),
                    Item('context.view_warning',
                         resizable = True,
                         visible_when = 'context.view_warning',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                 background_color = "#ffff99")),
                    Item('context.view_error',
                         resizable = True,
                         visible_when = 'context.view_error',
                         editor = ColorTextEditor(foreground_color = "#000000",
                                                  background_color = "#ff9191")))

@provides(IView)
class GaussianMixture2DPluginView(PluginViewMixin, GaussianMixture2DView):
    handler_factory = Callable(GaussianMixture2DViewHandler)
    op = Instance(IOperation, fixed = True)
    subset = DelegatesTo('op', transient = True)
    by = DelegatesTo('op', status = True)
    xchannel = DelegatesTo('op', 'xchannel', transient = True)
    xscale = DelegatesTo('op', 'x_channel_scale', transient = True)
    ychannel = DelegatesTo('op', 'ychannel', transient = True)
    yscale = DelegatesTo('op', 'y_channel_scale', transient = True)
    
    def plot_wi(self, wi):
        if wi.result:
            if wi.current_view_plot_names:
                self.plot(wi.result, plot_name = wi.current_plot)
            else:
                self.plot(wi.result)
        else:
            if wi.current_view_plot_names:
                self.plot(wi.previous_wi.result, plot_name = wi.current_plot)
            else:
                self.plot(wi.previous_wi.result)
        
    def enum_plots_wi(self, wi):
        if wi.result:
            try:
                return self.enum_plots(wi.result)
            except:
                return []
        else:
            try:
                return self.enum_plots(wi.previous_wi.result)
            except:
                return []
    

@provides(IOperationPlugin)
class GaussianMixture2DPlugin(Plugin, PluginHelpMixin):
    
    id = 'edu.mit.synbio.cytoflowgui.op_plugins.gaussian_2d'
    operation_id = 'edu.mit.synbio.cytoflow.operations.gaussian_2d'

    short_name = "2D Mixture Model"
    menu_group = "Gates"
    
    def get_operation(self):
        return GaussianMixture2DPluginOp()
    
    def get_icon(self):
        return ImageResource('gauss_2d')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    