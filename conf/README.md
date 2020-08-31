 A configuration file is a json file with the following fields. We also provide
 sample configuration files.
 - `eng_name`: Target JS engine ("chakra").
 - `eng_path`: ABSPATH to the JS engine.
 - `num_proc`: The number of processes (cores) to use for fuzzing.
 - `opt`: Additional options for executing a JS engine.
 - `seed_dir`: ABSPATH to the directory containing seed JS files.
 - `timeout`: Timeout for executing a JS code.
 - `tmp_dir`: ABSPATH for saving preprocessed data.
