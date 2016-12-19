﻿# Copyright (c) Microsoft. All rights reserved.

# Licensed under the MIT license. See LICENSE.md file in the project root
# for full license information.
# ==============================================================================

import numpy as np
import os
import sys
import platform
import argparse
from cntk.io import ReaderConfig, ImageDeserializer, FULL_DATA_SWEEP
from cntk import distributed
from cntk.device import set_default_device, gpu

abs_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(abs_path, "..", "..", "..", "..", "Examples", "Image", "Classification", "ConvNet", "Python"))
from ConvNet_CIFAR10_DataAug_Distributed import train_and_test_cifar_convnet


def run_cifar_convnet_distributed(epochs, block_samples, num_quantization_bits, distributed_after_samples):
    try:
        base_path = os.path.join(os.environ['CNTK_EXTERNAL_TESTDATA_SOURCE_DIRECTORY'],
                                *"Image/CIFAR/v0/cifar-10-batches-py".split("/"))
        # N.B. CNTK_EXTERNAL_TESTDATA_SOURCE_DIRECTORY has {train,test}_map.txt
        #      and CIFAR-10_mean.xml in the base_path.
    except KeyError:
        base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                *"../../../../Examples/Image/DataSets/CIFAR-10".split("/"))

    base_path = os.path.normpath(base_path)
    os.chdir(os.path.join(base_path, '..'))

    mean=os.path.join(base_path, 'CIFAR-10_mean.xml')
    train_data=os.path.join(base_path, 'train_map.txt')
    test_data=os.path.join(base_path, 'test_map.txt')

    from _cntk_py import set_computation_network_trace_level, set_fixed_random_seed, force_deterministic_algorithms
    set_computation_network_trace_level(1) 
    set_fixed_random_seed(1)  # BUGBUG: has no effect at present  # TODO: remove debugging facilities once this all works
    #force_deterministic_algorithms()
    # TODO: do the above; they lead to slightly different results, so not doing it for now

    return train_and_test_cifar_convnet(mean=mean, train_data=train_data, test_data=test_data, max_epochs=epochs, distributed_after_samples=distributed_after_samples, num_quantization_bits=num_quantization_bits, block_samples=block_samples)


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-q', '--quantize_bit', required=False, default=32, type=int)

    parser.add_argument('-e', '--epochs', required=False, default=2, type=int)
    parser.add_argument('-b', '--block_samples', required=False, type=int, default=0)
    parser.add_argument('-a', '--distributed_after', type=int, required=False, default='0')

    args = vars(parser.parse_args())
    num_quantization_bits = int(args['quantize_bit'])

    block_samples = int(args['block_samples'])
    distributed_after_samples=int(args['distributed_after'])

    assert distributed.Communicator.rank() < distributed.Communicator.num_workers()
    set_default_device(gpu(0)) # force using GPU-0 in test for speed
    run_cifar_convnet_distributed(epochs=epochs, block_samples=block_samples, num_quantization_bits=num_quantization_bits, distributed_after_samples=distributed_after_samples)

    distributed.Communicator.finalize()
    
