import torch
import torch.nn as nn
import numpy as np
import argparse
from models.convnext3d import (
    convnext3d_atto, 
    convnext3d_femto, 
    convnext3d_pico, 
    convnext3d_nano, 
    convnext3d_tiny
)
from monai.data import (
    ThreadDataLoader,
    CacheDataset,
    partition_dataset_classes,
    list_data_collate
)
from sklearn.model_selection import StratifiedGroupKFold
from data.splits import GroupStratifiedSplit
from data.datasets import CacheSeqDataset
from data.utils import (
    DatasetPreprocessor, 
    convert_to_dict, 
    convert_to_seqdict, 
    SequenceBatchCollater
)
from utils import cosine_scheduler, get_params_groups

def load_backbone(
        args: argparse.Namespace,
        dino_pretraining: bool = False
    ) -> nn.Module | Tuple[nn.Module]:

    in_chans = 1 if dino_pretraining else len(args.mod_list)

    if args.arch == 'atto':
        student = convnext3d_atto(
            in_chans=in_chans, kernel_size=args.kernel_size, drop_path_rate=args.stochastic_depth, use_v2=args.use_v2, eps=args.epsilon)
        teacher = convnext3d_atto(
            in_chans=in_chans, kernel_size=args.kernel_size, use_v2=args.use_v2, eps=args.epsilon)
    elif args.arch == 'femto':
        student = convnext3d_femto(
            in_chans=in_chans, kernel_size=args.kernel_size, drop_path_rate=args.stochastic_depth, use_v2=args.use_v2, eps=args.epsilon)
        teacher = convnext3d_femto(
            in_chans=in_chans, kernel_size=args.kernel_size, use_v2=args.use_v2, eps=args.epsilon)
    elif args.arch == 'pico':
        student = convnext3d_pico(
            in_chans=in_chans, kernel_size=args.kernel_size, drop_path_rate=args.stochastic_depth, use_v2=args.use_v2, eps=args.epsilon)
        teacher = convnext3d_pico(
            in_chans=in_chans, kernel_size=args.kernel_size, use_v2=args.use_v2, eps=args.epsilon)
    elif args.arch == 'nano':
        student = convnext3d_nano(
            in_chans=in_chans, kernel_size=args.kernel_size, drop_path_rate=args.stochastic_depth, use_v2=args.use_v2, eps=args.epsilon)
        teacher = convnext3d_nano(
            in_chans=in_chans, kernel_size=args.kernel_size, use_v2=args.use_v2, eps=args.epsilon)
    elif args.arch == 'tiny':
        student = convnext3d_tiny(
            in_chans=in_chans, kernel_size=args.kernel_size, drop_path_rate=args.stochastic_depth, use_v2=args.use_v2, eps=args.epsilon)
        teacher = convnext3d_tiny(
            in_chans=in_chans, kernel_size=args.kernel_size, use_v2=args.use_v2, eps=args.epsilon)
    
    if dino_pretraining:
        return student, teacher
    else:
        return student

def load_data(
        args: argparse.Namespace,
        device: torch.device,
        test: bool = False,
        pretraining: bool = False,
        partial: bool = False
    ) -> tuple:

    '''
    Load training objects.

    Args:
        args (argparse.Namespace): Command line arguments.

    Returns:
        tuple: Training objects consisting of the datasets, dataloaders, the model, and the performance metric.
    '''
    folds = range(args.k_folds) if args.k_folds > 0 else range(1)
    if test:
        phases = ['test']
    else:
        phases = ['train','val'] if args.k_folds > 0 else ['train']

    preprocessor = DatasetPreprocessor(
        data_dir=args.data_dir, 
        partial=True if partial else False)
    data_dict, label_df = preprocessor.load_data(
        modalities=args.mod_list, 
        keys=['label','delta'], 
        file_name='lirads.csv' if pretraining else 'labels.csv',
        verbose=False)
    default_dict, default_df = DatasetPreprocessor(data_dir=args.data_dir).load_data(
        modalities=['DWI_b0','DWI_b150','DWI_b400','DWI_b800'], 
        keys=['label','delta'], 
        file_name='labels.csv')
    default_dev, default_test = GroupStratifiedSplit(split_ratio=0.75).split_dataset(default_df)
    test = label_df[label_df['patient_id'].isin(default_test['patient_id'])]
    dev = label_df[-label_df['patient_id'].isin(test['patient_id'])]
    if args.k_folds > 1:
        cv_folds = StratifiedGroupKFold(n_splits=args.k_folds, shuffle=True, random_state=args.seed).split(dev, y=dev['label'], groups=dev['patient_id'])
        indices = [(dev.iloc[train_idx], dev.iloc[val_idx]) for train_idx, val_idx in list(cv_folds)]
        split_dict = [convert_to_dict([indices[k][0], indices[k][1]], data_dict=data_dict, split_names=phases) for k in folds]
    elif args.k_folds == 1:
        train, val = GroupStratifiedSplit(split_ratio=0.8).split_dataset(dev)
        split_dict = [convert_to_dict([train, val], data_dict=data_dict, split_names=phases, verbose=True) for k in folds]
    else:
        split_dict = [convert_to_dict([dev], data_dict=data_dict, split_names=phases, verbose=True) for k in folds]
    if test:
        split_dict = [convert_to_dict([test], data_dict=data_dict, split_names=phases, verbose=True) for k in folds]
    seq_split_dict = [convert_to_seqdict(split_dict[k], args.mod_list, phases) for k in folds]

    class_dict = {x: [[patient['label'] for patient in split_dict[k][x]] for k in folds] for x in phases}
    seq_class_dict = {x: [[max(patient['label']) for patient in seq_split_dict[k][x][0]] for k in folds] for x in phases}
    seq_split_dict = {x: [partition_dataset_classes(
        data=split_dict[k][x] if partial else seq_split_dict[k][x][0],
        classes=class_dict[k][x] if partial else seq_class_dict[x][k],
        num_partitions=dist.get_world_size(),
        shuffle=True,
        even_divisible=False
        )[dist.get_rank()] for k in folds] for x in phases}
    if partial:
        datasets = {x: [CacheDataset(
            data=split_dict[x][k], 
            transform=dino_transforms(
                modalities=args.mod_list, 
                device=device,
                global_crop_size=ensure_tuple_rep(args.global_crop_size, 3),
                local_crop_size=ensure_tuple_rep(args.local_crop_size, 3)),
            num_workers=8,
            copy_cache=False
            ) for k in folds] for x in phases}
    else:
        datasets = {x: [CacheSeqDataset(
            data=seq_split_dict[x][k],
            image_keys=args.mod_list,
            transform=transforms(
                dataset=x, 
                modalities=args.mod_list,
                device=device,
                crop_size=ensure_tuple_rep(args.global_crop_size, 3)),
            num_workers=8,
            copy_cache=False
            ) for k in folds] for x in phases}
    dataloader = {x: [ThreadDataLoader(
        datasets[x][k], 
        batch_size=(args.batch_size if x == 'train' else 1), 
        shuffle=(True if x == 'train' else False),   
        drop_last=(True if x == 'train' else False),   
        num_workers=0,
        collate_fn=(SequenceBatchCollater(
            keys=['image','label','delta'], 
            seq_length=args.seq_length) if x == 'train' & not partial else list_data_collate)
        ) for k in folds] for x in phases}
    _, counts = np.unique(seq_class_dict['train'][0], return_counts=True)
    pos_weight = counts[1] / counts.sum()

    return dataloader, pos_weight

def load_objs(
        args: argparse.Namespace,
        model: nn.Module,
        learning_rate: float = 1e-4,
        pos_weight: float | List[float] | None = None
    ) -> tuple:

    if args.loss_fn == 'bce':
        train_fn = BinaryCELoss(weights=pos_weight, label_smoothing=args.label_smoothing)
    elif args.loss_fn == 'focal':
        train_fn = FocalLoss(gamma=args.gamma, alpha=pos_weight, label_smoothing=args.label_smoothing)
    elif args.loss_fn == 'mse':
        train_fn = nn.MSELoss()
    elif args.loss_fn == 'dino':
        train_fn = DINOLoss(
            out_dim=args.out_dim,
            num_crops=4,
            num_steps=args.num_steps,
            teacher_temp=args.teacher_temp,
            teacher_warmup_temp=args.teacher_warmup_temp,
            teacher_warmup_steps=int(args.warmup_steps * 2))
    params = get_params_groups(model)
    optimizer = optim.AdamW(params, lr=learning_rate, weight_decay=args.weight_decay)
    lr_schedule = cosine_scheduler(
        base_value=learning_rate,
        final_value=args.min_learning_rate,
        steps=args.num_steps,
        warmup_steps=args.warmup_steps)
    wd_schedule = cosine_scheduler(
        base_value=args.weight_decay,
        final_value=args.max_weight_decay,
        steps=args.num_steps)
    m_schedule = cosine_scheduler(
        base_value=args.teacher_momentum,
        final_value=1,
        steps=args.num_steps)
    schedules = [lr_schedule, wd_schedule, m_schedule]
    return loss_fn, optimizer, schedules