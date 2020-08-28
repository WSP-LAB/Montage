# Montage

Montage is a JavaScript (JS) engine fuzzer that mutates a seed JS abstract
syntax tree (AST) by leveraging a neural network language model. The model is
trained on a set of JS regression tests to learn the underlying commonalities of
the JS tests that previously triggered JS engine bugs. Thus, Montage aims to
mutate a seed AST such that the resulting AST reflects the commonalities of the
trained JS tests. The key intuition behind our approach is that a JS code
similar to the previous bug-triggering JS code may trigger another bug. For more
details, please refer to our
[paper](https://leeswimming.com/papers/lee-sec20.pdf), "Montage: A Neural
Network Language Model-Guided JavaScript Engine Fuzzer", which appeared in
USENIX Security 2020.

## Installation
Montage works on a machine running Linux with NVIDIA graphic cards. It is tested
on a machine running Ubuntu 20.04 with GTX Titan XP GPUs. We currently support
ChakraCore only and have a plan to support V8, SpiderMonkey, and JavaScriptCore
shortly. To get ready for running Montage, please run the following commands:

```
$ sudo apt update
$ sudo apt install python3 python3-pip nodejs npm
$ npm install esprima@4.0.0 escodegen@1.9.1
$ git clone https://github.com/WSP-LAB/Montage
$ cd Montage
$ pip3 install -r requirement.txt
```
## Dataset

We provide dataset used in our experiments (Sec. 7.2-7.5) in this
[repository](https://github.com/WSP-LAB/js-test-suite).

## Usage

### Configuration file
Please refer to this
[link](https://github.com/WSP-LAB/Montage/blob/master/conf/README.md) for
writing a configuration file.

### Phase I

Phase I parses each JS file into an AST and then divides the AST into fragments.
As a result, Montage represents each JS code as a sequence of fragments on which
a neural network language model is trained.

```
$ cd Montage/src
$ python3 main.py --opt preprocess --config CONFIG_PATH
```

### Phase II
We will release the code for Phase II shortly.

### Phase III
We will release the code for Phase III shortly.

## Authors
This research project has been conducted by [WSP Lab](https://wsp-lab.github.io)
and [SoftSec Lab](https://softsec.kaist.ac.kr) at KAIST.

* [Suyoung Lee](https://leeswimming.com/)
* [HyungSeok Han](https://daramg.gift/)
* [Sang Kil Cha](https://softsec.kaist.ac.kr/~sangkilc/)
* [Sooel Son](https://sites.google.com/site/ssonkaist/home)

## Citation
To cite our paper:
```
@INPROCEEDINGS{lee:usenixsec:2020,
  author = {Suyoung Lee and HyungSeok Han and Sang Kil Cha and Sooel Son},
  title = {{Montage}: A Neural Network Language Model-Guided {JavaScript} Engine Fuzzer},
  booktitle = {Proceedings of the {USENIX} Security Symposium},
  pages = {2613--2630},
  year = 2020
}
```
