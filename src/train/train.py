import os
import random
import sys
import time

import torch
import numpy as np
from torch.nn import CrossEntropyLoss
from torch.optim import SGD
from torch.optim.lr_scheduler import ExponentialLR
from tqdm import tqdm

from train.model import LSTM
from utils import data2tensor
from utils import get_node_type
from utils import load_pickle
from utils import make_dir
from utils.logger import print_msg

def arr2data(seed_data):
  data_pairs = []

  for frag_seq, frag_info_seq in seed_data:
    if len(frag_seq) == 1: continue
    input_frag_seq = frag_seq[:-1]
    output_frag_seq = frag_seq[1:]

    data_pairs += [((input_frag_seq, frag_info_seq),
                    output_frag_seq)]

  data_pairs.sort(key=lambda x: len(x[0][0]),
                  reverse=True)
  inputs, outputs = zip(*data_pairs)
  return inputs, outputs

def pad_input(batch):
  input_batch, output_batch = batch
  input_frag_batch, frag_info_batch = zip(*input_batch)
  (input_frag_batch,
   seq_len_batch) = pad_sequence(input_frag_batch)
  output_batch, _ = pad_sequence(output_batch)

  pfrag_batch, type_batch = [], []
  for frag_info_seq in frag_info_batch:
    pfrag_seq, type_seq = zip(*frag_info_seq)
    pfrag_batch += [pfrag_seq]
    type_batch += [type_seq]

  pfrag_batch, _ = pad_sequence(pfrag_batch)
  type_batch, _ = pad_sequence(type_batch)
  return (input_frag_batch,
          pfrag_batch, type_batch,
          output_batch, seq_len_batch)

def pad_sequence(batch):
  max_time_step = len(batch[0])
  padded_batch, seq_len = [], []
  for seq in batch:
    padded_seq = []
    for i in range(max_time_step):
      if i < len(seq):
        padded_seq += [seq[i]]
      else:
        padded_seq += [0]
    padded_batch += [padded_seq]
    seq_len += [len(seq)]
  return padded_batch, seq_len

def repackage_hidden(h):
  if isinstance(h, torch.Tensor):
    return h.detach()
  else:
    return tuple(repackage_hidden(v) for v in h)

class ModelTrainer:
  def __init__(self, conf):
    self._batch_size = conf.batch_size
    self._emb_size = conf.emb_size
    self._epoch = conf.epoch
    self._gamma = conf.gamma
    self._lr = conf.lr
    self._momentum = conf.momentum
    self._num_gpu = conf.num_gpu
    self._split_size = conf.split_size
    self._weight_decay = conf.weight_decay

    self._train_data_path = os.path.join(conf.data_dir,
                                         'train_data.p')
    self._model_dir = os.path.join(conf.data_dir,
                                   'models')
    make_dir(self._model_dir)

  def arr2batch(self, seed_data):
    inputs, outputs = arr2data(seed_data)
    batches = self.data2batch(inputs, outputs)
    return batches

  def backward_pass(self, loss, optimizer):
    # Average across batch and time step
    index = torch.nonzero(loss)
    loss = loss[index]
    loss = torch.mean(loss)

    # Backward pass
    loss.backward()
    optimizer.step()

  def build_type_mask(self):
    type_mask = []
    type_size = len(self._type_list)
    for frag in self._oov_frag_list:
      frag_type_mask = [0 for i in range(type_size)]
      # Fragments
      if type(frag) == dict:
        frag_type = get_node_type(frag)
      # Out of vocabularies
      else:
        frag_type = frag
      type_idx = self._type_dict[frag_type]
      frag_type_mask[type_idx] = 1
      type_mask += [frag_type_mask]
    return type_mask

  def data2batch(self, inputs, outputs):
    batches = []
    for start in range(0, len(inputs), self._batch_size):
      end = start + self._batch_size
      input_batch = inputs[start:end]
      output_batch = outputs[start:end]
      batches += [(input_batch, output_batch)]
    return batches

  def init_model(self):
    self.print_config()

    type_mask = self.build_type_mask()
    loss = CrossEntropyLoss(reduction='none')
    vocab_size = len(self._oov_frag_list)
    batch_per_gpu = int(self._emb_size / self._num_gpu)
    model = LSTM(vocab_size, self._emb_size,
                 type_mask, loss, batch_per_gpu)
    model.cuda()

    optimizer = SGD(model.parameters(),
                    lr=self._lr,
                    momentum=self._momentum,
                    weight_decay=self._weight_decay)
    scheduler = ExponentialLR(optimizer,
                              gamma=self._gamma)

    return model, optimizer, scheduler

  def load_data(self):
    train_data = load_pickle(self._train_data_path)
    (oov_seed_dict,
     self._oov_frag_list,
     self._type_list,
     self._type_dict) = train_data

    seed_data = list(oov_seed_dict.values())
    train, test = self.split_data(seed_data)

    return train, test

  def print_config(self):
    vocab_size = len(self._oov_frag_list)
    msg = '# of Vocabularies: %d' % vocab_size
    print_msg(msg, 'INFO')

    msg = 'Embedding Size = %d' % self._emb_size
    print_msg(msg, 'INFO')

    msg = 'Initial LR = %f' % self._lr
    print_msg(msg, 'INFO')

    msg = 'LR Decay Factor = %f' % self._gamma
    print_msg(msg, 'INFO')

    msg = 'Momentum = %f' % self._momentum
    print_msg(msg, 'INFO')

    msg = 'L2 Regularization Penalty = %f\n' % self._weight_decay
    print_msg(msg, 'INFO')

  def print_metrics(self, mode, epoch,
                    total_loss, pplx, total_diff, acc):
    msg = '%s Loss at Epoch %d = %f' % (mode, epoch, total_loss)
    print_msg(msg, 'INFO')

    msg = '%s Perplexity at Epoch %d = %f' % (mode, epoch, pplx)
    print_msg(msg, 'INFO')

    msg = '%s Top K Difference at Epoch %d = %f' % (mode, epoch, total_diff)
    print_msg(msg, 'INFO')

    msg = '%s Accuracy at Epoch %d = %f\n' % (mode, epoch, acc)
    print_msg(msg, 'INFO')

  def process_data(self, train, test):
    train_batch = self.arr2batch(train)
    test_batch = self.arr2batch(test)
    return train_batch, test_batch

  def run_epoch(self, model, batches, epoch,
                optimizer=None, scheduler=None, mode=None):
    total_cross_entropy = 0.0
    total_diff = 0.0
    total_acc = 0.0
    num_val = 0
    is_train = (optimizer != None)
    if is_train:
      batch_iter = tqdm(batches)
      model.train()
    else:
      batch_iter = batches
      model.eval()

    for batch in batch_iter:
      padded_batch = pad_input(batch)
      (input_frag_chunks,
       pfrag_chunks, type_chunks,
       output_chunks) = map(self.split_batch, padded_batch[:4])
      seq_len_chunks = padded_batch[4]

      num_val += sum(seq_len_chunks)

      hidden = None
      seq_len_chunks = self.split_length(seq_len_chunks)
      data_chunks = zip(input_frag_chunks,
                        pfrag_chunks, output_chunks,
                        seq_len_chunks, type_chunks)

      for data_chunk in data_chunks:
        # Zero out grads
        model.zero_grad()

        (input_frag_chunk,
         pfrag_chunk, output_chunk,
         seq_len_chunk) = map(data2tensor, data_chunk[:4])
        type_chunk = data2tensor(data_chunk[4],
                                 tensor_type='Float')

        # Forward pass
        res = model(input_frag_chunk,
                    pfrag_chunk, type_chunk,
                    hidden, output_chunk, seq_len_chunk)

        hidden, pred, cross_entropy_loss, top_k_loss = res
        hidden = repackage_hidden(hidden)
        if is_train:
          loss = top_k_loss + cross_entropy_loss
          self.backward_pass(loss, optimizer)
        total_diff += float(torch.sum(top_k_loss))
        total_cross_entropy += float(torch.sum(cross_entropy_loss))
        total_acc += float(torch.sum(pred))

    if is_train:
      scheduler.step()

    total_loss = (total_diff + total_cross_entropy) / num_val
    pplx = np.exp(total_cross_entropy / num_val)
    acc = total_acc / num_val
    total_diff = total_diff / num_val

    self.print_metrics(mode, epoch,
                       total_loss, pplx, total_diff, acc)
    return pplx

  def save_model(self, model, epoch):
    mname = 'epoch-%d.model' % epoch
    model_path = os.path.join(self._model_dir, mname)
    torch.save(model, model_path)

  def split_batch(self, batch):
    chunks = []
    max_len = len(batch[0])
    for start in range(0, max_len, self._split_size):
      end = start + self._split_size
      chunk = [seq[start:end] for seq in batch]
      chunks += [chunk]
    return chunks

  def split_data(self, seed_data):
    random.shuffle(seed_data)
    length = len(seed_data)
    size = int(length / 10)

    train = seed_data[size:]
    test = seed_data[:size]

    return train, test

  def split_length(self, seq_len_batch):
    chunks = []
    while seq_len_batch[0] > 0:
      chunk = []
      for idx, seq_len in enumerate(seq_len_batch):
        if seq_len >= self._split_size:
          chunk += [self._split_size]
          seq_len_batch[idx] -= self._split_size
        else:
          chunk += [seq_len]
          seq_len_batch[idx] = 0
      chunks += [chunk]
    return chunks

  def train(self):
    train, test = self.load_data()
    train_batch, test_batch = self.process_data(train, test)
    model, optimizer, scheduler = self.init_model()
    prev_pplx = sys.maxsize

    for epoch in range(1, self._epoch + 1):
      msg = 'Epoch %d' % epoch
      print_msg(msg, 'INFO')

      self.run_epoch(model, train_batch, epoch,
                     optimizer=optimizer, scheduler=scheduler,
                     mode='Train')
      with torch.no_grad():
        test_pplx = self.run_epoch(model, test_batch, epoch,
                                   mode='Test')

      if prev_pplx > test_pplx:
        prev_pplx = test_pplx
        self.save_model(model, epoch)
