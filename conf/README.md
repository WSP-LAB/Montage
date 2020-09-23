 A configuration file is a json file with the following fields. We also provide
 sample configuration files.
 - `bug_dir`: ABSPATH for saving found bugs.
 - `data_dir`: ABSPATH for saving preprocessed data.
 - `eng_name`: Target JS engine ("chakra", "v8", "moz", "jsc").
 - `eng_path`: ABSPATH to the JS engine.
 - `max_ins`: The maximum number of fragments to append.
 - `model_path`: The path to the saved model to use for fuzzing.
 - `batch_size`: The batch size to use for training.
 - `emb_size`: The embedding dimension for each fragment.
 - `epoch`: The maximum number of epochs for training.
 - `gamma`: The multiplicative factor of learning rate decay.
 - `lr`: The initial learning rate.
 - `momentum`: The momentum factor for SGD.
 - `split_size`: The size of each split. Montage splits each sequence into
   multiple sequences for training efficiency.
 - `weight_decay`: Weight decay (L2 penalty).
 - `num_gpu`: The number of GPUs to use for fuzzing.
 - `num_proc`: The number of processes (cores) to use for fuzzing.
 - `opt`: Additional options for executing a JS engine.
 - `seed_dir`: ABSPATH to the directory containing seed JS files.
 - `timeout`: Timeout for executing a JS code.
 - `top_k`: The number of candidate fragments.
