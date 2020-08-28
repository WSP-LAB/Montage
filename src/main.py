import argparse
import os
import signal
import sys

from preprocess.preprocess import Preprocessor
from utils.config import Config

def get_args():
  arg_parser = argparse.ArgumentParser()
  arg_parser.add_argument('--opt', choices=['preprocess', 'train', 'fuzz'],
  	  	                  required=True)
  arg_parser.add_argument('--config', required=True)
  return arg_parser.parse_args(sys.argv[1:])

def handler(sigint, frame):
  os._exit(1)

if __name__ == '__main__':
  # Add a SIGINT handler
  signal.signal(signal.SIGINT, handler)

  # Increase max recursion depth limit
  sys.setrecursionlimit(10000)

  args = get_args()
  config_path = args.config
  conf = Config(config_path)

  p = Preprocessor(conf)
  p.preprocess()
