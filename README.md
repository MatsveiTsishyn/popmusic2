
# PoPMuSiC2

Python wrapper for running **PoPMuSiC-2** and **BeAtMuSiC** **mutational analysis**.  

## Installation and Usage

Install with,
```bash
pip install .
```

Then run,
```python
xxx
```

We also provide a few CLI commands, see explanations with,
```bash
xxx
```

## PoPMuSiC2 executable configuration

The package looks for a valid PoPMuSiC executable through the global CONFIG object defined in [popmusic2/config.py](popmusic2/config.py).

You can add candidate executable paths there in `CONFIG.music_candidate_paths`, or pass a custom path directly to the functions via `custom_music_path`.

The first valid executable found is cached in `CONFIG.music_path` and reused automatically.

## Main PoPMuSiC commands exposed by the package


## Mutation-based workflows


## Mutation and chain formats

Mutation strings use the convention:

- `A123V` for a single substitution
- `A123V:K204L` for multiple substitutions in one model

Chain pairs for interaction analysis use:

- `A:B`
- `AB:C`

These are passed to the relevant binding-affinity workflows and validated before execution.


