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
Created on Feb 11, 2015

@author: brian
"""

import sys, multiprocessing, StringIO, os, logging, traceback, threading

from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

import matplotlib

# We want matplotlib to use our backend
matplotlib.use('module://cytoflowgui.matplotlib_backend')

# getting real tired of the matplotlib deprecation warnings
import warnings
warnings.filterwarnings('ignore', '.*is deprecated and replaced with.*')

from traits.api import push_exception_handler
from envisage.core_plugin import CorePlugin
from envisage.ui.tasks.tasks_plugin import TasksPlugin
from pyface.image_resource import ImageResource

from flow_task import FlowTaskPlugin
from cytoflow_application import CytoflowApplication
from op_plugins import ImportPlugin, ThresholdPlugin, RangePlugin, \
                       Range2DPlugin, PolygonPlugin, BinningPlugin, \
                       GaussianMixture1DPlugin, GaussianMixture2DPlugin, \
                       BleedthroughLinearPlugin, BleedthroughPiecewisePlugin, \
                       BeadCalibrationPlugin
from view_plugins import HistogramPlugin, Histogram2DPlugin, ScatterplotPlugin, \
                         BarChartPlugin, Stats1DPlugin, Kde1DPlugin, Kde2DPlugin, \
                         ViolinPlotPlugin, TablePlugin, Stats2DPlugin

import cytoflowgui.matplotlib_backend as mpl_backend
# import cytoflowgui.workflow as workflow
from cytoflowgui import multiprocess_logging 

# from https://github.com/pyinstaller/pyinstaller/wiki/Recipe-Multiprocessing

# Module multiprocessing is organized differently in Python 3.4+
try:
    # Python 3.4+
    if sys.platform.startswith('win'):
        import multiprocessing.popen_spawn_win32 as forking
    else:
        import multiprocessing.popen_fork as forking
except ImportError:
    import multiprocessing.forking as forking

if sys.platform.startswith('win'):
    # First define a modified version of Popen.
    class _Popen(forking.Popen):
        def __init__(self, *args, **kw):
            if hasattr(sys, 'frozen'):
                # We have to set original _MEIPASS2 value from sys._MEIPASS
                # to get --onefile mode working.
                os.putenv('_MEIPASS2', sys._MEIPASS)
            try:
                super(_Popen, self).__init__(*args, **kw)
            finally:
                if hasattr(sys, 'frozen'):
                    # On some platforms (e.g. AIX) 'os.unsetenv()' is not
                    # available. In those cases we cannot delete the variable
                    # but only set it to the empty string. The bootloader
                    # can handle this case.
                    if hasattr(os, 'unsetenv'):
                        os.unsetenv('_MEIPASS2')
                    else:
                        os.putenv('_MEIPASS2', '')

    # Second override 'Popen' class with our modified version.
    forking.Popen = _Popen
    
def log_notification_handler(obj, trait_name, old, new):
    
    (exc_type, exc_value, tb) = sys.exc_info()
    logging.debug('Exception occurred in traits notification '
                  'handler for object: %s, trait: %s, old value: %s, '
                  'new value: %s.\n%s\n' % ( object, trait_name, old, new,
                  ''.join( traceback.format_exception(exc_type, exc_value, tb) ) ) )

    err_string = traceback.format_exception_only(exc_type, exc_value)[0]
    err_loc = traceback.format_tb(tb)[-1]
    err_ctx = threading.current_thread().name
    
    logging.error("Error: {0}\nLocation: {1}Thread: {2}" \
                  .format(err_string, err_loc, err_ctx) )
    
def log_excepthook(typ, val, tb):
    tb_str = "".join(traceback.format_tb(tb))
    logging.debug("Global exception: {0}\n{1}: {2}"
                  .format(tb_str, typ, val))
    
    tb_str = traceback.format_tb(tb)[-1]
    logging.error("Error: {0}: {1}\nLocation: {2}Thread: Main"
                  .format(typ, val, tb_str))
    
                         
def run_gui():
    multiprocessing.freeze_support()
    
    from pyface.qt import qt_api
    
    if qt_api == "pyside":
        print "Cytoflow uses PyQT; but it is trying to use PySide instead."
        print " - Make sure PyQT is installed."
        print " - If both are installed, and you don't need both, uninstall PySide."
        print " - If you must have both installed, select PyQT by setting the"
        print "   environment variable QT_API to \"pyqt\""
        print "   * eg, on Linux, type on the command line:"
        print "     QT_API=\"pyqt\" python run.py"
        print "   * on Windows, try: "
        print "     setx QT_API \"pyqt\""

        sys.exit(1)
    
    # if we're frozen, add _MEIPASS to the pyface search path for icons etc
    if getattr(sys, 'frozen', False):
        from pyface.resource_manager import resource_manager
        resource_manager.extra_paths.append(sys._MEIPASS)
        
    # install a global (gui) error handler for traits notifications
    push_exception_handler(handler = log_notification_handler,
                           reraise_exceptions = False, 
                           main = True)
    
    sys.excepthook = log_excepthook
        
    debug = ("--debug" in sys.argv)

    plugins = [CorePlugin(), TasksPlugin(), FlowTaskPlugin(debug = debug)]    
    
    # reverse of the order on the toolbar
    view_plugins = [TablePlugin(),
                    Stats2DPlugin(),
                    Stats1DPlugin(),
                    BarChartPlugin(),
                    ViolinPlotPlugin(),
                    Kde2DPlugin(),
                    Kde1DPlugin(),
                    Histogram2DPlugin(),
                    ScatterplotPlugin(),
                    HistogramPlugin()]
    
    plugins.extend(view_plugins)
    
    op_plugins = [BeadCalibrationPlugin(),
                  BleedthroughPiecewisePlugin(),
                  BleedthroughLinearPlugin(),
                  GaussianMixture2DPlugin(),
                  GaussianMixture1DPlugin(),
                  BinningPlugin(),
                  PolygonPlugin(),
                  Range2DPlugin(),
                  RangePlugin(),
                  ThresholdPlugin(),
                  ImportPlugin()]

    plugins.extend(op_plugins)
    
    app = CytoflowApplication(id = 'edu.mit.synbio.cytoflow',
                              plugins = plugins,
                              icon = ImageResource('icon'))
    app.run()
    
    logging.shutdown()
    
# def remote_main(workflow_parent_conn, mpl_parent_conn, log_q):
    
#     # connect the remote pipes
#     workflow.parent_conn = workflow_parent_conn
#     mpl_backend.parent_conn = mpl_parent_conn
#     
#     # setup logging
#     h = multiprocess_logging.QueueHandler(log_q)  # Just the one handler needed
#     logging.getLogger().addHandler(h)
#     logging.getLogger().setLevel(logging.DEBUG)
#     
#     # install a global (gui) error handler for traits notifications
#     push_exception_handler(handler = log_notification_handler,
#                            reraise_exceptions = False, 
#                            main = True)
#     
#     sys.excepthook = log_excepthook
    
    # run the remote workflow
    #workflow.RemoteWorkflow().run()


if __name__ == '__main__':
    run_gui()

        
    # set up the child process


    # connect the local pipes
#     workflow.child_conn = workflow_child_conn       
#     mpl_backend.child_conn = mpl_child_conn   


        
    # start the child process
#     remote_process = multiprocessing.Process(target = remote_main,
#                                              name = "remote",
#                                              args = (workflow_parent_conn, 
#                                                      mpl_parent_conn, 
#                                                      log_q))
#     remote_process.daemon = True
#     remote_process.start()    
    

