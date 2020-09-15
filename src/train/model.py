import torch
import torch.nn as nn
from torch.nn.utils.rnn import pack_padded_sequence

def is_none(tensor):
  return type(tensor) == type(None)

def reform_batch(data, length):
  data = pack_padded_sequence(data, length,
                              batch_first=True)
  data = data.data
  return data

def reform_hidden(hidden, idx):
  dim = hidden[0].shape[1:]
  hidden = reshape_hidden(hidden, dim,
                          expand=False)
  hidden = tuple(map(lambda x: reform_tensor(x, idx),
                     hidden))

  dim = hidden[0].shape
  hidden = reshape_hidden(hidden, dim)
  return hidden

def reform_tensor(tensor, idx):
  return tensor[:idx]

def remove_null_seq(input_frag_chunk,
                    pfrag_chunk, type_chunk,
                    hidden, output_chunk, seq_len_chunk):
  seq_len_chunk = seq_len_chunk.tolist()
  if 0 not in seq_len_chunk:
    return (input_frag_chunk,
            pfrag_chunk, type_chunk,
            hidden, output_chunk, seq_len_chunk)

  null_idx = seq_len_chunk.index(0)

  org_chunk = (input_frag_chunk,
               pfrag_chunk, type_chunk,
               output_chunk, seq_len_chunk)
  new_chunk = tuple(map(lambda x: reform_tensor(x, null_idx),
                        org_chunk))
  (input_frag_chunk,
   pfrag_chunk, type_chunk,
   output_chunk, seq_len_chunk) = new_chunk

  if not is_none(hidden):
    hidden = reform_hidden(hidden, null_idx)

  return (input_frag_chunk,
          pfrag_chunk, type_chunk,
          hidden, output_chunk, seq_len_chunk)

def reshape_hidden(hidden, dim, expand=True):
  row, col = dim
  if expand:
    hidden = tuple(map(lambda x: x.view(1, row, col),
                       hidden))
  else:
    hidden = tuple(map(lambda x: x.view(row, col),
                       hidden))
  return hidden

class LSTM(nn.Module):
  def __init__(self, vocab_size, embedding_dim,
               type_mask, loss_function, batch_per_gpu):
    super(LSTM, self).__init__()
    # Input Layer
    self.embeddings = nn.Embedding(vocab_size, embedding_dim)

    # Hidden Layer
    self.lstm = nn.LSTM(input_size=embedding_dim,
                        hidden_size=embedding_dim)

    # Output Layer
    self.out_dim = embedding_dim * 2 + 1
    self.fc = nn.Linear(self.out_dim, vocab_size)

    self.vocab_size = vocab_size
    self.type_mask = type_mask
    self.softmax = nn.Softmax(dim=1)
    self.loss_function = loss_function
    self.embedding_dim = embedding_dim
    self.batch_per_gpu = batch_per_gpu

  def build_mask(self, type_chunk, time_step, vocab_size):
    # Frag & Type Matrix
    type_mask = torch.cuda.ByteTensor(self.type_mask)
    tmask = type_chunk.view(-1).long()

    # Mask Type Matching Frags
    tmask = torch.index_select(type_mask, 1, tmask)
    tmask = torch.transpose(tmask, 0, 1)
    tmask = tmask.view(time_step, vocab_size)
    tmask = tmask.float()
    return tmask

  def forward(self, input_frag_chunk, pfrag_chunk, type_chunk,
              hidden, output_chunk, seq_len_chunk):
    batch = remove_null_seq(input_frag_chunk, pfrag_chunk,
                            type_chunk, hidden,
                            output_chunk, seq_len_chunk)
    (input_frag_chunk, pfrag_chunk,
     type_chunk, hidden,
     output_chunk, seq_len_chunk) = batch

    # Input Layer
    embeds = self.embeddings(input_frag_chunk)
    embeds = pack_padded_sequence(embeds, seq_len_chunk,
                                  batch_first=True)

    # Hidden Layer
    if is_none(hidden):
      out, hidden = self.lstm(embeds)
    else:
      out, hidden = self.lstm(embeds, hidden)
    out = out.data

    # Get the embed of parent frags
    pfrag_chunk = self.embeddings(pfrag_chunk)
    pfrag_chunk = reform_batch(pfrag_chunk, seq_len_chunk)

    # Reform data
    type_chunk = reform_batch(type_chunk, seq_len_chunk)
    output_chunk = reform_batch(output_chunk, seq_len_chunk)
    type_chunk = type_chunk.view(-1, 1)

    # Concatenate Additional Features
    out = torch.cat((out, pfrag_chunk, type_chunk), dim=1)

    # Output Layer
    out = self.fc(out)

    # Compute loss
    cross_entropy = self.get_cross_entropy(out, output_chunk)
    top_k_loss = self.get_top_k_loss(out, type_chunk)
    pred = self.get_accuracy(out, output_chunk)
    return hidden, pred, cross_entropy, top_k_loss

  def get_accuracy(self, out, output_chunk):
    pred = torch.argmax(out, 1)
    pred = pred.view(-1)
    pred = torch.eq(output_chunk, pred)
    return pred

  def get_cross_entropy(self, out, output_chunk):
    time_step, vocab_size = out.shape
    out = out.view(-1, vocab_size)
    output_chunk = output_chunk.view(-1)
    cross_entropy = self.loss_function(out, output_chunk)
    return cross_entropy

  def get_top_k_loss(self, out, type_chunk):
    time_step, vocab_size = out.shape

    # Prob Out for Type Matching Frags
    prob_out = self.softmax(out)
    tmask = self.build_mask(type_chunk, time_step, vocab_size)
    type_out = tmask * prob_out

    # Prob Out for Top K Frags
    tmask, _ = torch.sort(tmask, dim=1, descending=True)
    prob_out, _ = torch.sort(prob_out, dim=1, descending=True)
    k_out = tmask * prob_out

    # Compute Top K Loss
    top_k_loss = torch.sum(k_out, dim=1)
    top_k_loss -= torch.sum(type_out, dim=1)
    return top_k_loss

  def run(self, inputs, hidden=None, parent_idx=None, frag_type=None):
    # Input Layer
    embeds = self.embeddings(inputs)
    embeds = embeds.view(-1, 1, self.embedding_dim)

    # Hidden Layer
    if is_none(hidden):
      out, hidden = self.lstm(embeds)
      return hidden
    else:
      out, hidden = self.lstm(embeds, hidden)

    # Concatenate Additional Features
    parent_idx = self.embeddings(parent_idx)
    parent_idx = parent_idx.view(1, -1, self.embedding_dim)
    frag_type = frag_type.view(1, -1, 1)
    out = out.view(1, -1, self.embedding_dim)
    out = torch.cat((out, parent_idx, frag_type), dim=2)

    # Output Layer
    out = out.contiguous().view(-1, self.out_dim)
    out = self.fc(out)
    out = out.view(1, -1, self.vocab_size)
    return out, hidden

