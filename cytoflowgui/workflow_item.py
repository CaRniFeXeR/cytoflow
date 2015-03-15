'''
Created on Mar 15, 2015

@author: brian
'''

from traits.api import HasTraits, Instance, ListInstance
from traitsui.api import View, Handler

from cytoflow import Experiment
from cytoflow.operations.i_operation import IOperation
from cytoflow.views.i_view import IView

class WorkflowItem(HasTraits):
    """        
    The basic unit of a Workflow: wraps an operation and a list of views.
    """
    
    # the operation this Item wraps
    operation = Instance(IOperation)
    
    # a handler for constraining *operation*'s traitsui interface 
    handler = Instance(Handler)
    
    # the Experiment that is the result of applying *operation* to a 
    # previous Experiment
    result = Instance(Experiment)
    
    # a list of IViews against the output of this operation
    views = ListInstance(IView)
    
    traits_view = View('operation',
                       handler = handler)
    
