# Replicating the experiments
1. Open .bashrc or .zshrc (depending which shell you use) and add a line “export $DATA_DIR={path-of-the-data-dir}.
2. Generate the commands for the desired experiment using the `scripts/fcmi_scripts.py` script.
3. Parse the result of the experiment using the `scripts/fcmi_parse_results.py` script.
4. Use the `notebooks/fcmi-plots.ipynb` to generate plots from the parsed results.

# Requirements
* Basic libraries such as `numpy`, `scipy`, `tqdm`, `matplotlib`, and `seaborn`.
* We used `Pytorch 1.7.0`, but higher versions should work too.
