#!/g/kreshuk/lukoianov/miniconda3/envs/inferno/bin/python3

#BASIC IMPORTS
import argparse
import os
import subprocess
import sys
 
#INTERNAL IMPORTS
from src.datasets import CentriollesDatasetOn
from src.utils import get_basic_transforms, log_info
import src.implemented_models as impl_models

#INFERNO IMPORTS
import torch
from inferno.trainers.basic import Trainer
from torch.utils.data import DataLoader
from inferno.trainers.callbacks.logging.tensorboard import TensorboardLogger

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run learning of simple CNN implementation')

    parser.add_argument('--model_name', type=str, default='', help='Name of the model from models dir')
    parser.add_argument('--test', action='store_true', help='Test this model on simpler dataset')
    parser.add_argument('--id', type=str, default='default', help='Unique net id to save')
    parser.add_argument('--img_size', type=int, default=60, help='Size of input images')

    args = parser.parse_args()
    log_info( 'Params: ' + str(args))

    train_tr, test_tr = get_basic_transforms()
    if args.test:
        train_ds = CentriollesDatasetOn(transform=train_tr, 
                                        pos_dir='dataset/mnist/1', 
                                        neg_dir='dataset/mnist/0', inp_size=args.img_size)
        test_ds  = CentriollesDatasetOn(transform=test_tr , 
                                        pos_dir='dataset/mnist/1', 
                                        neg_dir='dataset/mnist/0', inp_size=args.img_size, train=False)
        log_info('Test bags dataset is used')
    else:
        train_ds = CentriollesDatasetOn(transform=train_tr, 
                                        pos_dir='dataset/artificial/train_pos/', 
                                        neg_dir='dataset/artificial/train_neg/', 
                                        inp_size=args.img_size, all_data=True)
        test_ds  = CentriollesDatasetOn(transform=test_tr , 
                                        pos_dir='dataset/artificial/test_pos/', 
                                        neg_dir='dataset/artificial/test_neg/', 
                                        inp_size=args.img_size,  all_data=True)
        log_info('ILC dataset is used')  
    
    train_dl = DataLoader(train_ds, batch_size=4, shuffle=True, num_workers=0)
    test_dl  = DataLoader(test_ds,  batch_size=4, shuffle=True, num_workers=0)

    log_info('Datasets are initialized!')


    ### DIRS AND MODEL
    exec("model = impl_models.%s" % (args.model_name))


    model_dir = os.path.join('models', args.model_name)
    curent_model_dir = os.path.join(model_dir, args.id)
    log_info('Model will be saved to %s' % (curent_model_dir))
    log_info('  + Number of params: {}'.format(sum([p.data.nelement() for p in model.parameters()])))

    weight_dir = os.path.join(curent_model_dir, 'weights')
    log_info('Weights will be saved to %s' % (weight_dir))
    if not os.path.exists(weight_dir):
        os.mkdir(weight_dir)
    logs_dir = os.path.join(curent_model_dir, 'logs')
    if not os.path.exists(logs_dir):
        os.mkdir(logs_dir)
    log_info('Logs will be saved to %s' % (logs_dir))


    # Build trainer
    trainer = Trainer(model) \
        .build_criterion('CrossEntropyLoss') \
        .build_metric('CategoricalError') \
        .build_optimizer('Adam') \
        .validate_every((2, 'epochs')) \
        .save_every((5, 'epochs')) \
        .save_to_directory(model_dir) \
        .set_max_num_epochs(10000) \
        .build_logger(TensorboardLogger(log_scalars_every=(1, 'iteration'),
                                        log_images_every=(1, 'epoch')),
                                        log_directory=logs_dir)

    # Bind loaders
    trainer \
        .bind_loader('train', train_dl) \
        .bind_loader('validate', test_dl)

    if torch.cuda.is_available():
        trainer.cuda()

    trainer.fit()