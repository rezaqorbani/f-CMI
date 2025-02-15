from tqdm import tqdm
import os
import argparse
import pickle

import numpy as np
import torch

from nnlib.nnlib import utils
from nnlib.nnlib.matplotlib_utils import import_matplotlib

matplotlib, plt = import_matplotlib()

from modules.bound_utils import estimate_fcmi_bound_classification, estimate_sgld_bound
from scripts.fcmi_train_classifier import mnist_ld_schedule, \
    cifar_resnet50_ld_schedule  # for pickle to be able to load LD methods
import methods


class NestedDict(dict):
    def __missing__(self, key):
        self[key] = type(self)()
        return self[key]


def compute_acc(preds, mask, dataset):
    labels = [y for x, y in dataset]
    labels = torch.tensor(labels).long()
    indices = 2*np.arange(len(mask)) + mask
    acc = (preds[indices].argmax(dim=1) == labels[indices]).float().mean()
    return utils.to_numpy(acc)


def get_fcmi_results_for_fixed_z(n, epoch, seed, args):
    train_accs = []
    val_accs = []
    preds = []
    masks = []
    all_examples = None  # will be needed after this loop to dump some extra information
    for S_seed in range(args.n_S_seeds):
        dir_name = f'n={n},seed={seed},S_seed={S_seed}'
        dir_path = os.path.join(args.results_dir, args.exp_name, dir_name)
        if not os.path.exists(dir_path):
            print(f"Did not find results for {dir_name}")
            continue

        with open(os.path.join(dir_path, 'saved_data.pkl'), 'rb') as f:
            saved_data = pickle.load(f)
        print(list(saved_data.keys()))

        model = utils.load(path=os.path.join(dir_path, 'checkpoints', f'epoch{epoch - 1}.mdl'),
                           methods=methods, device=args.device)

        if 'all_examples_wo_data_aug' in saved_data:
            all_examples = saved_data['all_examples_wo_data_aug']
        else:
            all_examples = saved_data['all_examples']

        cur_preds = utils.apply_on_dataset(model=model, dataset=all_examples,
                                           batch_size=args.batch_size)['pred']
        cur_mask = saved_data['mask']
        cur_train_acc = compute_acc(preds=cur_preds, mask=cur_mask, dataset=all_examples)
        cur_val_acc = compute_acc(preds=cur_preds, mask=1-cur_mask, dataset=all_examples)
        print(cur_train_acc, cur_val_acc)

        preds.append(cur_preds)
        masks.append(cur_mask)
        train_accs.append(cur_train_acc)
        val_accs.append(cur_val_acc)

    fcmi_bound, list_of_mis = estimate_fcmi_bound_classification(masks=masks, preds=preds,
                                                                 num_examples=n, num_classes=args.num_classes,
                                                                 return_list_of_mis=True)

  

    return {
        'exp_train_acc': np.mean(train_accs),
        'exp_val_acc': np.mean(val_accs),
        'exp_gap': np.mean(train_accs) - np.mean(val_accs),
        'fcmi_bound': fcmi_bound,
        'list_of_mis': list_of_mis
    }


def get_fcmi_results_for_fixed_model(n, epoch, args):
    results = []
    for seed in range(args.n_seeds):
        cur = get_fcmi_results_for_fixed_z(n=n, epoch=epoch, seed=seed, args=args)
        results.append(cur)
    return results


def get_sgld_results_for_fixed_model(n, epoch, args):
    results = []

    for seed in range(args.n_seeds):
        for S_seed in range(args.n_S_seeds):
            if S_seed >= 4:
                continue  # these guys didn't track gradient variance to save time

            dir_name = f'n={n},seed={seed},S_seed={S_seed}'
            dir_path = os.path.join(args.results_dir, args.exp_name, dir_name)
            if not os.path.exists(dir_path):
                print(f"Did not find results for {dir_name}")
                continue

            with open(os.path.join(dir_path, 'saved_data.pkl'), 'rb') as f:
                saved_data = pickle.load(f)

            model = utils.load(path=os.path.join(dir_path, 'checkpoints', f'epoch{epoch - 1}.mdl'),
                               methods=methods, device=args.device)

            if 'all_examples_wo_data_aug' in saved_data:
                all_examples = saved_data['all_examples_wo_data_aug']
            else:
                all_examples = saved_data['all_examples']

            cur_preds = utils.apply_on_dataset(model=model, dataset=all_examples,
                                               batch_size=args.batch_size)['pred']
            cur_mask = saved_data['mask']
            cur_train_acc = compute_acc(preds=cur_preds, mask=cur_mask, dataset=all_examples)
            cur_val_acc = compute_acc(preds=cur_preds, mask=1-cur_mask, dataset=all_examples)

            cur_result = {}
            cur_result['train_acc'] = cur_train_acc
            cur_result['val_acc'] = cur_val_acc
            cur_result['gap'] = cur_val_acc - cur_train_acc

            sgld_bound = estimate_sgld_bound(n=n, batch_size=args.batch_size,
                                             model=model)
            cur_result['sgld_bound'] = sgld_bound
            results.append(cur_result)

    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--device', '-d', default='cuda', help='specifies the main device')
    parser.add_argument('--exp_name', type=str, required=True)
    parser.add_argument('--results_dir', type=str, default='results')
    parser.add_argument('--batch_size', type=int, default=256)
    parser.set_defaults(parse=True)
    args = parser.parse_args()
    print(args)

    if args.exp_name == "fcmi-cats-and-dogs-CNN-deterministic":
        args.n_seeds = 5
        args.n_S_seeds = 30
        args.ns = [75, 150, 300, 600]
        args.epochs = np.arange(1, 11) * 2
        args.num_classes = 2
 
    else:
        raise ValueError(f"Unexpected exp_name: {args.exp_name}")

    # parse quantities needed for the f-CMI bound
    results = NestedDict()  # indexing with n, epoch
    for n in tqdm(args.ns):
        for epoch in tqdm(args.epochs, leave=False):
            results[n][epoch] = get_fcmi_results_for_fixed_model(n=n, epoch=epoch, args=args)
    results_file_path = os.path.join(args.results_dir, args.exp_name, 'results.pkl')
    with open(results_file_path, 'wb') as f:
        pickle.dump(results, f)


if __name__ == '__main__':
    main()
