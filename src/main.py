import argparse
import os
import signal
import sys
import torch

from fuzz.fuzz import fuzz
from preprocess.preprocess import Preprocessor
from train.train import ModelTrainer
from utils.config import Config
from utils.logger import print_msg

def exec_fuzz(conf):
  fuzz(conf)

def exec_preprocess(conf):
    preprocessor = Preprocessor(conf)
    preprocessor.preprocess()

def exec_train(conf):
  trainer = ModelTrainer(conf)
  trainer.train()

def get_args():
  arg_parser = argparse.ArgumentParser()
  arg_parser.add_argument('--opt', choices=['preprocess', 'train', 'fuzz'],
  	  	                  required=True)
  arg_parser.add_argument('--config', required=True)
  return arg_parser.parse_args(sys.argv[1:])

def handler(sigint, frame):
  os._exit(1)

def main():
  if not torch.cuda.is_available():
    print_msg('Montage only supports CUDA-enabled machines',
              'ERROR')
    sys.exit(1)

  # Add a SIGINT handler
  signal.signal(signal.SIGINT, handler)

  # Increase max recursion depth limit
  sys.setrecursionlimit(10000)

  args = get_args()
  config_path = args.config
  conf = Config(config_path)

  if args.opt == 'preprocess':
    exec_preprocess(conf)
  elif args.opt == 'train':
    exec_train(conf)
  elif args.opt == 'fuzz':
    exec_fuzz(conf)

if __name__ == '__main__':
  main()
