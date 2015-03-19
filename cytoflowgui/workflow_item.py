'''
Created on Mar 15, 2015

@author: brian
'''

from traits.api import HasTraits, Instance, List, Str, DelegatesTo, Event, Enum
from traitsui.api import View, Handler

from cytoflow import Experiment
from cytoflow.operations.i_operation import IOperation
from cytoflow.views.i_view import IView

class WorkflowItem(HasTraits):
    """        
    The basic unit of a Workflow: wraps an operation and a list of views.
    
    This object is part of the workflow *model* -- as such, it is implemented
    *reactively*.  No methods; just reactions to traits being changed by
    the UI and handler.
    """
    
    # the operation's id
    id = DelegatesTo('operation')
    
    # the operation's name
    name = DelegatesTo('operation')
    
    # the operation this Item wraps
    operation = Instance(IOperation)
    
    # a handler for constraining *operation*'s traitsui interface 
    handler = Instance(Handler)
    
    # the Experiment that is the result of applying *operation* to a 
    # previous Experiment
    result = Instance(Experiment)
    
    # a list of IViews against the output of this operation
    views = List(IView)
    
    # the previous WorkflowItem in the workflow
    # self.result = self.apply(previous.result)
    previous = Instance('WorkflowItem')
    
    # the next WorkflowItem in the workflow
    next = Instance('WorkflowItem')
    
    # are we valid?
    valid = Enum("valid", "updating", "invalid", default = "invalid")
    
    # an event for the previous WorkflowItem to tell this one to update
    update = Event
    
    traits_view = View(handler = handler)
        
    def _valid_changed(self, old, new):
        if old == "valid" and new == "invalid" and self.next is not None:
            self.next.valid = "invalid"
    
    def _update_fired(self):
        """
        Called when the previous WorkflowItem has changed its result.
        """
        self.valid = "updating"
        
        # re-run the operation (TODO)
        
        # update the views (TODO)
        
        # tell the next WorkflowItem to go
        self.next.update = True
    
