import json
import os

from utils import read

class Config:
  def __init__(self, conf_path):
    conf = self.load_conf(conf_path)
    self.data_dir = conf['data_dir']
    self.eng_name = conf['eng_name']
    self.eng_path = conf['eng_path']
    self.num_proc = conf['num_proc']
    self.timeout = conf['timeout']
    self.opt = conf['opt']
    self.seed_dir = conf['seed_dir']

    self.ast_dir = os.path.join(self.data_dir, 'ast')
    self.log_dir = os.path.join(self.data_dir, 'log')

  def load_conf(self, conf_path):
    conf = read(conf_path, 'r')
    dec = json.JSONDecoder()
    conf = dec.decode(conf)
    return conf
