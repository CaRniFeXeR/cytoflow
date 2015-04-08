"""
Created on Feb 24, 2015

@author: brian
"""
from traits.api import provides
from traitsui.api import Controller, View, Item, CheckListEditor
from envisage.api import Plugin, contributes_to
from pyface.api import ImageResource

from cytoflow.operations import IOperation, HlogTransformOp
from cytoflowgui.op_plugins import OpHandlerMixin, IOperationPlugin, OP_PLUGIN_EXT

@provides(IOperation)
class HLogHandler(Controller, OpHandlerMixin):
    """
    classdocs
    """
    
    def default_traits_view(self):
        return View(Item('object.name'),
                    Item('object.channels',
                         editor = CheckListEditor(name='handler.previous_channels',
                                                  cols = 2),
                         style = 'custom'))
    
@provides(IOperationPlugin)
class HLogPlugin(Plugin):
    """
    class docs
    """
    
    id = 'edu.mit.synbio.cytoflowgui.op.hlog'
    operation_id = 'edu.mit.synbio.cytoflow.op.hlog'
    
    short_name = "Hyperlog"
    menu_group = "Transformations"
     
    def get_operation(self):
        ret = HlogTransformOp()
        ret.handler_factory = HLogHandler
        return ret
    
    def get_icon(self):
        return ImageResource('hlog')
    
    @contributes_to(OP_PLUGIN_EXT)
    def get_plugin(self):
        return self
    

    
        