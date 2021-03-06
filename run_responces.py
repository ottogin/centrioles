#!/g/kreshuk/lukoianov/miniconda3/envs/inferno/bin/python3

# BASIC IMPORTS
import argparse
import os
import subprocess
import sys

# INTERNAL IMPORTS
from src.datasets import ResponcesDataset
from src.utils import log_info
import src.implemented_models as impl_models

# INFERNO IMPORTS
import torch
from inferno.trainers.basic import Trainer
from torch.utils.data import DataLoader
from inferno.trainers.callbacks.logging.tensorboard import TensorboardLogger
from inferno.trainers.callbacks.scheduling import AutoLR

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run learning of simple CNN implementation')

    parser.add_argument('--model_name', type=str, default='', help='Name of the model from models dir')
    parser.add_argument('--id', type=str, default='default', help='Unique net id to save')

    args = parser.parse_args()
    log_info('Params: ' + str(args))

    train_ds = ResponcesDataset(impl_models.ICL_DenseNet_3fc)
    test_ds = ResponcesDataset(impl_models.ICL_DenseNet_3fc, train=False)
    train_dl = DataLoader(train_ds, batch_size=4, shuffle=True, num_workers=0)
    test_dl = DataLoader(test_ds,  batch_size=4, shuffle=True, num_workers=0)
    log_info('Datasets are initialized!')

    # DIRS AND MODEL
    exec("model = impl_models.%s" % (args.model_name))

    model_dir = os.path.join('models', args.model_name)
    curent_model_dir = os.path.join(model_dir, args.id)
    log_info('Model will be saved to %s' % (curent_model_dir))
    log_info(' + Number of params: {}'.format(sum([p.data.nelement() for p in model.parameters()])))

    weight_dir = os.path.join(curent_model_dir, 'weights')
    log_info('Weights will be saved to %s' % (weight_dir))
    if not os.path.exists(weight_dir):
        os.mkdir(weight_dir)
    logs_dir = os.path.join(curent_model_dir, 'logs')
    if not os.path.exists(logs_dir):
        os.mkdir(logs_dir)
    log_info('Logs will be saved to %s' % (logs_dir))

    # Build trainer
    logger = TensorboardLogger(log_scalars_every=(1, 'iteration'),
                               log_images_every=None,
                               log_histograms_every=None)

    def log_hist(self, tag, values=1, step=1, bins=1000):
        """Logs the histogram of a list/vector of values."""
        pass
    logger.log_histogram = log_hist

    trainer = Trainer(model)\
        .build_criterion('CrossEntropyLoss') \
        .build_metric('CategoricalError') \
        .build_optimizer('Adam') \
        .validate_every((400, 'iterations')) \
        .save_every((400, 'iterations')) \
        .save_to_directory(weight_dir) \
        .set_max_num_epochs(10000) \
        .build_logger(logger, log_directory=logs_dir) \
        .register_callback(AutoLR(0.9, (1, 'epochs'),
                           consider_improvement_with_respect_to='previous'))

    # Bind loaders
    trainer \
        .bind_loader('train', train_dl) \
        .bind_loader('validate', test_dl)

    if torch.cuda.is_available():
        trainer.cuda()

    trainer.fit()
