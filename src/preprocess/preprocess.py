import os
from multiprocessing import Pool

from preprocess import aggregate
from preprocess import execute
from preprocess import fragmentize
from preprocess import normalize
from preprocess import oov
from preprocess import strip
from preprocess import triage
from utils import make_dir
from utils import store_pickle
from utils.logger import print_msg
from utils.parse import Parser

class Preprocessor:
  def __init__(self, conf):
    self._pool = Pool(conf.num_proc)
    self._conf = conf

  def remove_js_with_errors(self):
    execute.main(self._pool, self._conf)
    triage.main(self._conf)

  def parse(self):
    parser = Parser(self._conf)
    parser.parse()

  def strip_eval(self):
    strip.main(self._pool, self._conf)

  def normalize_ast(self):
    normalize.main(self._pool, self._conf)

  def fragment_ast(self):
    return fragmentize.main(self._pool, self._conf)

  def aggregate_frags(self, ast_data):
    aggregated_data = aggregate.main(ast_data)
    (self._seed_dict,
     self._frag_dict, self._frag_list,
     self._type_dict, self._type_list) = aggregated_data

  def mark_oov(self):
    renewed_data = oov.replace_uncommon(self._seed_dict,
                                        self._frag_list,
                                        self._frag_dict)
    (self._new_seed_dict,
     self._new_frag_dict, self._new_frag_list,
     self._oov_pool) = renewed_data

  def preprocess(self):
    print_msg('[1/8] Filtering out JS with errors')
    self.remove_js_with_errors()

    print_msg('[2/8] Parsing JS code into ASTs')
    self.parse()

    print_msg('[3/8] Stripping args of eval func calls')
    self.strip_eval()

    print_msg('[4/8] Normalizing identifiers')
    self.normalize_ast()

    print_msg('[5/8] Fragmentizing JS ASTs')
    ast_data = self.fragment_ast()

    print_msg('[6/8] Aggregating fragments')
    self.aggregate_frags(ast_data)
    self._pool.terminate()

    print_msg('[7/8] Replacing uncommon fragments')
    self.mark_oov()

    print_msg('[8/8] Writing data into files')
    self.write_data()

  def write_data(self):
    data_path = os.path.join(self._conf.data_dir,
                                'data.p')
    train_data_path = os.path.join(self._conf.data_dir,
                                    'train_data.p')
    seed_data_path = os.path.join(self._conf.data_dir,
                                  'seed.p')

    # Write a seed file
    seed = (self._seed_dict, self._frag_list,
            self._new_seed_dict)
    store_pickle(seed_data_path, seed)

    # Write a train data file
    train_data = (self._new_seed_dict,
                  self._new_frag_list,
                  self._type_list,
                  self._type_dict)
    store_pickle(train_data_path, train_data)

    # Write a data file
    data = (self._new_frag_list, self._new_frag_dict,
            self._oov_pool, self._type_dict)
    store_pickle(data_path, data)
