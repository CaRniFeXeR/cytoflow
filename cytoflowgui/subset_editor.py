'''
Created on Mar 23, 2015

@author: brian
'''

if __name__ == '__main__':
    from traits.etsconfig.api import ETSConfig
    ETSConfig.toolkit = 'qt4'

    import os
    os.environ['TRAITS_DEBUG'] = "1"

from traitsui.api import BasicEditorFactory, View, Group, UI, \
                         CheckListEditor, Item
from traitsui.qt4.editor import Editor
from traits.api import Instance, HasTraits, List, Float, Int, Str
from cytoflow import Experiment
from value_bounds_editor import ValuesBoundsEditor
import pandas as pd
import numpy as np

class _SubsetEditor(Editor):
    
    # the cytoflow.Experiment to construct the UI
    experiment = Instance(Experiment)
    
    # the UI for the Experiment metadata
    _ui = Instance(UI)
    
    # the object we create to represent the Experiment conditions
    _obj = Instance(HasTraits)
    
    def init(self, parent):
        """
        Finishes initializing the editor; create the underlying toolkit widget
        """
        
        self.sync_value(self.factory.experiment, 'experiment', 'from')
        
        # TODO - when loading, this gets called before the wi gets updated
        # with the operation's results; so we need a way to display a subset
        # that's not yet initialized.
        self._obj, group = self._get_view()
        
        self._ui = self._obj.edit_traits(kind='subpanel', 
                                         parent=parent,
                                         view=View(group))

        self._obj.on_trait_change(self._view_changed)
        self.control = self._ui.control
        
    def dispose(self):
        self._ui.dispose()
        self._ui = None
        self._obj.on_trait_change(self._view_changed, remove = True)
        super(_SubsetEditor, self).dispose()
        
    def update_editor(self):
        print "TODO - update editor with {0}".format(self.value)
        pass  #for the moment
        
    def _get_view(self):
        
        obj = HasTraits()   # the underlying object whose traits we're viewing
        group = Group()     # the TraitsUI Group with the editors in it
        
#         for name, dtype in self.experiment.conditions.iteritems():
#             if dtype == 'bool':
#                 values = [name + '-', name + '+']
#                 obj.add_trait(name, List(editor = CheckListEditor(
#                                                     values = values,
#                                                     cols = 2)))
#                 group.content.append(Item(name, 
#                                           style = 'custom'))
#                 
#             elif dtype == 'category':
#                 values = list(self.experiment[name].cat.categories)
#                 obj.add_trait(name, List(editor = CheckListEditor(
#                                                     values = values,
#                                                     cols = len(values))))
#                 group.content.append(Item(name, 
#                                           style = 'custom'))
#                 
#             elif dtype == 'float':
#                 values = list(np.sort(pd.unique(self.experiment[name])))
#                 obj.add_trait(name + "Min", Float(self.experiment[name].min()))
#                 obj.add_trait(name + "Max", 
#                               Float(default_value = self.experiment[name].max(),
#                                     editor = ValuesBoundsEditor( 
#                                                 values = values,
#                                                 low_name = name + "Min",
#                                                 high_name = name + "Max"))
#                             )
#                 group.content.append(Item(name + "Max", 
#                                           label = name, 
#                                           style = 'custom'))
#                 
#             elif dtype == 'int':
#                 values = list(np.sort(pd.unique(self.experiment[name])))
#                 obj.add_trait(name + "Min", Int(self.experiment[name].min()))
#                 obj.add_trait(name + "Max", 
#                               Int(default_value = self.experiment[name].max(),
#                                   editor = ValuesBoundsEditor(
#                                                 values = values,
#                                                 low_name = name + "Min",
#                                                 high_name = name + "Max"))
#                             )
#                 
#                 group.content.append(Item(name + "Max", 
#                                           label = name, 
#                                           style = 'custom'))
        
        return obj, group
    
    def _view_changed(self, name, new, old):
        
        # we want to spit out a value in a standard form so we can easily
        # parse it back in.
        
        subsets = []
        
        for name, dtype in self.experiment.conditions.iteritems(): 
            if dtype == 'bool':
                val = self._obj.trait_get(name)[name]
                if name + '+' in val and not name + '-' in val:
                    subsets.append("({0} == True)".format(name))
                elif name + '+' not in val and name + '-' in val:
                    subsets.append("({0} == False)".format(name))
                else:
                    # "name" is any value; dont' include specifier
                    pass
                
            elif dtype == 'category':
                val = self._obj.trait_get(name)[name]
                phrase = "("
                for cat in val:
                    if len(phrase) > 1:
                        phrase += " or "
                    phrase += "{0} == {1}".format(name, cat) 
                phrase += ")"
                
            elif dtype == 'float':
                min_val = self._obj.trait_get(name + "Min")[name + "Min"]
                max_val= self._obj.trait_get(name + "Max")[name + "Max"]
                subsets.append("({0} >= {1} and {0} <= {2})"
                               .format(name, min_val, max_val))
                
            elif dtype == 'int':
                min_val = self._obj.trait_get(name + "Min")[name + "Min"]
                max_val = self._obj.trait_get(name + "Max")[name + "Max"]
                subsets.append("({0} >= {1} and {0} <= {2})"
                               .format(name, min_val, max_val))
                
            self.value = " and ".join(subsets)
            print self.value                

class SubsetEditor(BasicEditorFactory):
    
    # the editor to be created
    klass = _SubsetEditor
    
    # the cytoflow.Experiment instance to build the UI
    experiment = Str
    
    