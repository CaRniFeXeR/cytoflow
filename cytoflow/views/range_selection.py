from traits.api import provides, HasTraits, Instance, Float, Bool, \
                       on_trait_change

from cytoflow.views.i_selectionview import ISelectionView
from cytoflow.views.i_view import IView

from matplotlib.widgets import SpanSelector
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.lines import Line2D

@provides(ISelectionView)
class RangeSelection(HasTraits):
    """Plots, and lets the user interact with, a selection on the X axis.
    
    Is it beautiful?  No, not yet.  Does it demonstrate the capabilities I
    desire?  Yes.
    
    Attributes
    ----------
    min : Float
        The minimum value of the range.
        
    max : Float
        The maximum value of the range.
        
    view : Instance(IView)
        the IView that this view is wrapping.  I suggest that if it's another
        ISelectionView, that its `interactive` property remain False. >.>
        
    interactive : Bool
        is this view interactive?  Ie, can the user set min and max
        with a mouse drag?
    """
    
    id = "edu.mit.synbio.cytoflow.views.range"
    friendly_id = "Range Selection"
    
    low = Float(None)
    high = Float(None)
    
    # internal state.
    _span = Instance(SpanSelector, transient = True)
    _low_line = Instance(Line2D, transient = True)
    _high_line = Instance(Line2D, transient = True)
    _hline = Instance(Line2D, transient = True)
        
    def plot(self, experiment, fig_num = None, **kwargs):
        """Plot self.view, and then plot the selection on top of it."""
        self.view.plot(experiment, fig_num, **kwargs)
        self._draw_span()

    def is_valid(self, experiment):
        """If the decorated view is valid, we are too."""
        return self.view.is_valid(experiment)
    
    @on_trait_change('low, high')
    def _draw_span(self):
        if not (self.low and self.high):
            return
        
        if self._low_line:
            self._low_line.remove()
        
        if self._high_line:
            self._high_line.remove()
            
        if self._hline:
            self._hline.remove()
            
        if self.low and self.high:
            self._low_line = plt.axvline(self.low, linewidth=3, color='grey')
            self._high_line = plt.axvline(self.high, linewidth=3, color='grey')
            
            ymin, ymax = plt.ylim()
            y = (ymin + ymax) / 2.0
            self._hline = plt.plot([self.low, self.high], 
                                   [y, y], 
                                   color='grey', 
                                   linewidth = 2)[0]
                                   
        plt.gcf().canvas.draw()
    
    @on_trait_change('interactive')
    def _interactive(self):
        if self.interactive:
            ax = plt.gca()
            self._span = SpanSelector(ax, 
                             onselect=self._onselect, 
                             direction='horizontal',
                             rectprops={'alpha':0.2,
                                        'color':'grey'},
                             span_stays=False,
                             useblit = True)
        else:
            self._span = None
        
    
    def _onselect(self, xmin, xmax): 
        """Update selection traits"""
        self.low = xmin
        self.high = xmax
        
if __name__ == '__main__':
    import seaborn as sns
    import cytoflow as flow
    import FlowCytometryTools as fc
    
    import matplotlib as mpl
    import matplotlib.pyplot as plt
    mpl.rcParams['savefig.dpi'] = 2 * mpl.rcParams['savefig.dpi']
    
    tube1 = fc.FCMeasurement(ID='Test 1', 
                             datafile='../../cytoflow/tests/data/Plate01/RFP_Well_A3.fcs')

    tube2 = fc.FCMeasurement(ID='Test 2', 
                           datafile='../../cytoflow/tests/data/Plate01/CFP_Well_A4.fcs')
    
    ex = flow.Experiment()
    ex.add_conditions({"Dox" : "float"})
    
    ex.add_tube(tube1, {"Dox" : 10.0})
    ex.add_tube(tube2, {"Dox" : 1.0})
    
    hlog = flow.HlogTransformOp()
    hlog.name = "Hlog transformation"
    hlog.channels = ['V2-A']
    ex2 = hlog.apply(ex)
    
    hist = flow.HistogramView()
    hist.name = "Hist"
    hist.channel = "V2-A"
    hist.huefacet = 'Dox'
    
    range = flow.RangeSelection(view = hist) 
    
    plt.ioff()
    range.plot(ex2)
    range.interactive = True
    plt.show()