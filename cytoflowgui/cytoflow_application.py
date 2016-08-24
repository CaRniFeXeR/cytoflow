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
Created on Mar 15, 2015

@author: brian
'''

import sys
from traceback import format_exception

from envisage.ui.tasks.api import TasksApplication
from pyface.api import error
from pyface.tasks.api import TaskWindowLayout
from traits.api import Bool, Instance, List, Property, push_exception_handler

from preferences import CytoflowPreferences

def gui_notification_handler(obj, name, old, new):
    (exc_type, exc_value, tb) = sys.exc_info()
    error(None, "An exception has occurred.  Please report a problem from the Help menu!\n\n" +
                ''.join(format_exception(exc_type, exc_value, tb, 3)))
    

class CytoflowApplication(TasksApplication):
    """ The cytoflow Tasks application.
    """

    # The application's globally unique identifier.
    id = 'edu.mit.synbio.cytoflow'

    # The application's user-visible name.
    name = 'Cytoflow'

    # Override two traits from TasksApplication so we can provide defaults, below

    # The default window-level layout for the application.
    default_layout = List(TaskWindowLayout)

    # Whether to restore the previous application-level layout when the
    # applicaton is started.
    always_use_default_layout = Property(Bool)
    
    def run(self):
        # install a global (gui) error handler for traits notifications
        push_exception_handler(handler = gui_notification_handler,
                               reraise_exceptions = True, 
                               main = True)
        
        # run the GUI
        super(CytoflowApplication, self).run()
    

    #### 'AttractorsApplication' interface ####################################

    preferences_helper = Instance(CytoflowPreferences)

    ###########################################################################
    # Private interface.
    ###########################################################################
    
    #### Trait initializers ###################################################

    def _default_layout_default(self):
        active_task = self.preferences_helper.default_task
        tasks = [ factory.id for factory in self.task_factories ]
        return [ TaskWindowLayout(*tasks,
                                  active_task = active_task,
                                  size = (800, 600)) ]

    def _preferences_helper_default(self):
        return CytoflowPreferences(preferences = self.preferences)

    #### Trait property getter/setters ########################################

    def _get_always_use_default_layout(self):
        return self.preferences_helper.always_use_default_layout
