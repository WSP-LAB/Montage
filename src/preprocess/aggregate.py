from utils import hash_frag
from utils import print_msg

class Aggregator:
  def __init__(self):
    self._frag_dict = {}
    self._frag_list = []
    self._hash_frag_list = set()
    self._type_dict = {}
    self._type_list = []

  def add_frag(self, node):
    hash_val = hash_frag(node)
    # New fragment
    if hash_val not in self._hash_frag_list:
      self._hash_frag_list.add(hash_val)
      frag_idx = self.get_frag_idx()
      self._frag_dict[hash_val] = frag_idx
      self._frag_list += [node]
    # Existing fragment, but different hash
    elif hash_val not in self._frag_dict:
      frag_idx = self._frag_list.index(node)
    # Existing fragment
    else:
      frag_idx = self._frag_dict[hash_val]
    return frag_idx

  def add_type(self, node_types):
    for node_type in node_types:
      if node_type not in self._type_list:
        self._type_dict[node_type] = self.get_type_idx()
        self._type_list += [node_type]

  def aggregate(self, ast_data):
    self._seed_dict = {}
    num_file = len(ast_data)
    for i, v in enumerate(ast_data):
      if v is None: continue
      file_name, _frag_seq, _frag_info_seq, _node_types = v
      frag_seq, frag_info_seq = [], []

      msg = '[%d/%d] %s' % (i + 1, num_file, file_name)
      print_msg(msg, 'INFO')

      # Build node type list & dict
      self.add_type(_node_types)

      # Build fragment list, dict
      for frag in _frag_seq:
        frag_idx = self.add_frag(frag)
        frag_seq += [frag_idx]

      # Build dataset for additional features
      for next_parent_idx, frag_type in _frag_info_seq:
        next_parent_frag = frag_seq[next_parent_idx]
        type_idx = self._type_dict[frag_type]
        frag_info = (next_parent_frag, type_idx)
        frag_info_seq += [frag_info]

      self._seed_dict[file_name] = (frag_seq, frag_info_seq)

  def get_data(self):
    return (self._seed_dict,
            self._frag_dict, self._frag_list,
            self._type_dict, self._type_list)

  def get_frag_idx(self):
    return len(self._frag_list)

  def get_type_idx(self):
    return len(self._type_list)

def main(ast_data):
  aggregator = Aggregator()
  aggregator.aggregate(ast_data)
  return aggregator.get_data()
