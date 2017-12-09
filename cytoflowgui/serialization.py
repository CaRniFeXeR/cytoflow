'''
Keep all the camel serialization bits together.
Created on Dec 2, 2017

@author: brian
'''

from textwrap import dedent
import logging
import pandas

from pyface.api import error

#### YAML serialization

from camel import Camel, CamelRegistry, YAML_TAG_PREFIX

# the camel registry singletons
camel_registry = CamelRegistry()
standard_types_registry = CamelRegistry(tag_prefix = YAML_TAG_PREFIX)

def load_yaml(path):
    with open(path, 'r') as f:
        data = Camel([camel_registry]).load(f.read())
        
    return data

def save_yaml(data, path):
    with open(path, 'w') as f:
        f.write(Camel([standard_types_registry,
                       camel_registry]).dump(data))

# camel adapters for traits lists, dicts, numpy types
from numpy import float64, int64, bool_
@standard_types_registry.dumper(float64, 'float', version = None)
def _dump_float(fl):
    return repr(float(fl)).lower()

@standard_types_registry.dumper(int64, 'int', version = None)
def _dump_int(i):
    return repr(int(i)).lower()

@standard_types_registry.dumper(bool_, 'bool', version = None)
def _dump_bool(b):
    return repr(bool(b)).lower()

from traits.trait_handlers import TraitListObject, TraitDictObject
from traits.api import Undefined

@standard_types_registry.dumper(TraitListObject, 'seq', version = None)
def _dump_list(tlo):
    return list(tlo)
 
@standard_types_registry.dumper(TraitDictObject, 'map', version = None)
def _dump_dict(tdo):
    return dict(tdo)

@camel_registry.dumper(Undefined.__class__, 'undefined', version = 1)
def _dump_undef(ud):
    return "Undefined"

@camel_registry.loader('undefined', version = 1)
def _load_undef(data, version):
    return Undefined

@camel_registry.dumper(pandas.Series, 'pandas-series', version = 1)
def _dump_series(s):
    return dict(index = list(s.index),
                data = list(s.values))
    
# this is quite simplistic.  i don't know if it works for hierarchical
# indices.
@camel_registry.loader('pandas-series', version = 1)
def _load_series(data, version):
    return pandas.Series(data = data['data'],
                         index = data['index'])
    


#### Jupyter notebook serialization

import nbformat as nbf
from yapf.yapflib.yapf_api import FormatCode

def save_notebook(workflow, path):
    nb = nbf.v4.new_notebook()
    
    # todo serialize here
    header = dedent("""\
        from cytoflow import *
        %matplotlib inline""")
    nb['cells'].append(nbf.v4.new_code_cell(header))
        
    for i, wi in enumerate(workflow):

        code = wi.operation.get_notebook_code(i)
        
        logging.debug("Op cell:")
        logging.debug(code)
        try:
            code = FormatCode(code, style_config = 'pep8')[0]
        except:
            error(parent = None,
                  message = "Had trouble serializing the {} operation"
                            .format(wi.operation.friendly_id))
        
        nb['cells'].append(nbf.v4.new_code_cell(code))   
                    
        for view in wi.views:
            if hasattr(wi.operation, 'default_view') and \
                wi.operation.default_view().id == view.id:
                continue

            code = view.get_notebook_code(i)
    
            logging.debug("View cell")
            logging.debug(code)
            try:
                code = FormatCode(code, style_config = 'pep8')[0]
            except:
                error(parent = None,
                      message = "Had trouble serializing the {} view of the {} operation"
                                 .format(view.friendly_id, wi.operation.friendly_id))
            
            nb['cells'].append(nbf.v4.new_code_cell(code))
            
    with open(path, 'w') as f:
        nbf.write(nb, f)

