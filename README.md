# Dependencies

All libraries are standard bar libraries used in plot_benchmark_results.ipynb

To plot benchmarks, install the following libraries:
```
pip install numpy pandas matplotlib
```
# Grammar

Grammars are stored in the ./grammar directory in .bnf format

To change a grammar, edit the following line in grammar_defs.py ...

```
_BNF_FILE = _THIS_DIR / "mathler_unconstrained.bnf"
```
... to the filename of your desired grammar. Keep in mind this project is intended for grammars which map to arithmetic expressions, and only accepts safely evaluating, 6 character expressions.

# CONFIG

The system runs off of a Global Config, config.py, which currently pulls it's values from the best autotuned config, found in the ./tunes directory.

# Running the Project

Ensuring your desired grammar and config is selected, running a demo game of the project is as simple as running:
```
python ./solver_demo.py
```
From the root directory

# Autotuning
Config parameters can be automatically tuned using the random parameter search strategy.

Running "run_autotune.py" from the root directory simulates 200 games, each with randomized configs.

The best performing config is saved to the ./tunes directory, which can then be pulled into the Global Config for running demo games.

# Benchmarking

Benchmarking is run from the ./benchmarking directory

Metrics are saved to 3 .csv files in the results directory, allowing us to track performance on per-game, per-guess and per-generation levels

To run a benchmark, run the following command from the ./benchmarks directory:
```
python -m benchmarking.run_benchmark --games 100 --seed 12345 --tag BENCHMARK_RUN_TAG --save-secrets
```
--games : number of games in this benchmark  
--seed : start seed for generating secret expressions  
--tag : results dir filename

# TESTS

The ./tests directory contains some simple test files to ensure our grammar, fitness and game engine functions are working as intended
