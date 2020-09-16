import collections

from utils import get_node_type
from utils import hash_frag
from utils.logger import print_msg

def collect_oov(seed_dict, frag_list):
  oov_types = set()
  hash_frag_list = set()
  oov_pool = {}

  sorted_frags, oov_idx = sort_frags(seed_dict)
  # For rare fragments
  for frag_idx in sorted_frags[oov_idx:]:
    frag = frag_list[frag_idx]
    node_type = get_node_type(frag)

    # Append to OoV pool
    if node_type not in oov_pool:
      oov_pool[node_type] = []
    oov_pool[node_type] += [frag]

    # Add OoV type
    oov_types.add(node_type)

    # Add to OoV fragment list
    hash_val = hash_frag(frag)
    hash_frag_list.add(hash_val)

  return sorted_frags, oov_types, hash_frag_list, oov_pool

def get_oov_idx(frag, frag_dict):
  frag_type = get_node_type(frag)
  return frag_dict[frag_type]

def is_oov(frag, hash_frag_list):
  hash_val = hash_frag(frag)
  return hash_val in hash_frag_list

def replace_uncommon(seed_dict, frag_list, frag_dict):
  # Collect OoV
  ret = collect_oov(seed_dict, frag_list)
  sorted_frags, oov_types, hash_frag_list, oov_pool = ret

  # Update frag_list & frag_dict
  ret = update_frags(sorted_frags, frag_list,
                     hash_frag_list, oov_types)
  new_frag_list, new_frag_dict = ret

  # Update ast_frags
  new_seed_dict = update_ast(seed_dict,
                             frag_list,
                             hash_frag_list,
                             new_frag_dict)

  return (new_seed_dict,
          new_frag_dict, new_frag_list,
          oov_pool)

def sort_frags(seed_dict):
  all_frags = []
  for frag_seq, _ in seed_dict.values():
    all_frags += frag_seq

  # Count fragments
  counter = collections.Counter(all_frags)
  frag_frq = []
  for key in counter:
    frag_frq += [(key, counter[key])]

  # Sort by frequencies
  frag_frq = sorted(frag_frq,
                    key = lambda x: x[1], reverse=True)
  sorted_frags, frq = zip(*frag_frq)
  oov_idx = frq.index(5)

  msg = 'OOV IDX = %d' % oov_idx
  print_msg(msg, 'INFO')
  return sorted_frags, oov_idx

def update_ast(seed_dict,
               frag_list, hash_frag_list, new_frag_dict):
  new_seed_dict = {}
  num_files = len(seed_dict.keys())
  for idx, file_name in enumerate(seed_dict.keys()):
    msg = '[%d/%d] %s' % (idx + 1, num_files, file_name)
    print_msg(msg, 'INFO')

    frag_seq, frag_info_seq = seed_dict[file_name]

    # Update frag_seq
    new_frag_seq = update_frag_seq(frag_seq,
                                   new_frag_dict,
                                   frag_list,
                                   hash_frag_list)
    # Update frag_info_seq
    new_frag_info_seq = update_frag_info(frag_info_seq,
                                         new_frag_dict,
                                         frag_list,
                                         hash_frag_list)
    new_seed_dict[file_name] = (new_frag_seq, new_frag_info_seq)
  return new_seed_dict

def update_frags(sorted_frags,
                 frag_list, hash_frag_list, oov_types):
  new_frag_list = []
  new_frag_dict = {}

  # Append frags not in OoV
  for frag_idx in sorted_frags:
    frag = frag_list[frag_idx]
    frag_type = get_node_type(frag)
    if not is_oov(frag, hash_frag_list):
      frag_idx = len(new_frag_list)
      new_frag_list += [frag]
      new_frag_dict[hash_frag(frag)] = frag_idx

  # Append OoVs
  for oov_type in oov_types:
    frag_idx = len(new_frag_list)
    new_frag_list += [oov_type]
    new_frag_dict[oov_type] = frag_idx

  return new_frag_list, new_frag_dict

def update_frag_info(frag_info_seq,
                     new_frag_dict, frag_list, hash_frag_list):
  new_frag_info_seq = []
  for parent_idx, frag_type in frag_info_seq:
    parent_frag = frag_list[parent_idx]
    if is_oov(parent_frag, hash_frag_list):
      parent_idx = get_oov_idx(parent_frag,
                               new_frag_dict)
    else:
      parent_idx = new_frag_dict[hash_frag(parent_frag)]
    frag_info = (parent_idx, frag_type)
    new_frag_info_seq += [frag_info]
  return new_frag_info_seq

def update_frag_seq(frag_seq,
                    new_frag_dict, frag_list, hash_frag_list):
  new_frag_seq = []
  for frag_idx in frag_seq:
    frag = frag_list[frag_idx]
    if is_oov(frag, hash_frag_list):
      frag_idx = get_oov_idx(frag, new_frag_dict)
    else:
      frag_idx = new_frag_dict[hash_frag(frag)]
    new_frag_seq += [frag_idx]
  return new_frag_seq
