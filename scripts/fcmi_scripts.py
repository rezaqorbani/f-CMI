import argparse

from nnlib.nnlib.data_utils.base import register_parser as register_fn


local_functions = {}  # storage for registering the functions below


#######################################################################################
#
#     MNIST 4 vs 9, CNN
#
# exp_name: fcmi-mnist-4vs9-CNN
#######################################################################################

@register_fn(local_functions, 'fcmi-cats-and-dogs-CNN')
def foo(deterministic=False, **kwargs):
    config_file = 'configs/binary-mnist-4layer-CNN.json'
    batch_size = 128
    n_epochs = 20
    save_iter = 2
    exp_name = "fcmi-cats-and-dogs-CNN"
    if deterministic:
        exp_name = exp_name + '-deterministic'
    dataset = 'cats-and-dogs'
    #which_labels = ' '

    command_prefix = f"python -um scripts.fcmi_train_classifier -c {config_file} -d cuda -b {batch_size} " \
                     f"-e {n_epochs} -s {save_iter} -v 10000 --exp_name {exp_name} -D {dataset} --optimizer adadelta " #\
                    # f"--which_labels {which_labels} "

    if deterministic:
        command_prefix += "--deterministic "

    n_seeds = 5
    n_S_seeds = 30
    ns = [75, 250, 1000, 4000]

    for n in ns:
        for seed in range(n_seeds):
            for S_seed in range(n_S_seeds):
                command = command_prefix + f"--n {n} --seed {seed} --S_seed {S_seed};"
                print(command)



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--exp_names', '-E', type=str, nargs='+', required=True)
    parser.add_argument('--deterministic', action='store_true', dest='deterministic')
    parser.add_argument('--shuffle_train_only_after_first_epoch', action='store_true',
                        dest='shuffle_train_only_after_first_epoch')
    args = parser.parse_args()

    for exp_name in args.exp_names:
        assert exp_name in local_functions
        local_functions[exp_name](**vars(args))


if __name__ == '__main__':
    main()
