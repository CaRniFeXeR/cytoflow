"""
Created on Mar 15, 2015

@author: brian
"""
from traits.api import Interface, Str, HasTraits, Instance, Property, \
                       cached_property
from cytoflowgui.workflow_item import WorkflowItem

OP_PLUGIN_EXT = 'edu.mit.synbio.cytoflow.op_plugins'

class IOperationPlugin(Interface):
    """
    Attributes
    ----------
    
    id : Str
        The Envisage ID used to refer to this plugin
        
    operation_id : Str
        Same as the "id" attribute of the IOperation this plugin wraps.
        
    short_name : Str
        The operation's "short" name - for menus and toolbar tool tips
        
    menu_group : Str
        If we were to put this op in a menu, what submenu to use?
        Not currently used.
    """
    
    operation_id = Str
    short_name = Str
    menu_group = Str

    def get_operation(self):
        """
        Return an instance of the IOperation that this plugin wraps, along
        with the factory for the handler
        """
        
        
    def get_default_view(self, op):
        """
        Return an IView instance set up to be the default view for the operation.
        
        Arguments
        ---------
        
        op: IOperation instance
            the operation to set up the view for
        """

    def get_icon(self):
        """
        
        """
        
class OpHandlerMixin(HasTraits):
    wi = Instance(WorkflowItem)
    
    # a Property wrapper around the wi.previous.result.channels
    # used to constrain the operation view (with an EnumEditor)
    previous_channels = Property(depends_on = 'wi.previous.result.channels')
    
    @cached_property
    def _get_previous_channels(self):
        if (not self.wi.previous) or (not self.wi.previous.result):
            return []
              
        return self.wi.previous.result.channels
    