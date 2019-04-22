import sys
import os
import numpy as np
import tensorflow as tf

from io_helpers import load_dataset, download_dataset, discover_and_setup_tfrecords
import harmonic_network_models

class settings():
    def __init__(self, opt):
        self.opt = opt
        self.data = {}
        self.__maybe_create('num_threads_per_queue', 1)
        #check that we have all the required options
        if 'deviceIdxs' in self.opt and \
            'dataset' in self.opt and \
            'model' in self.opt and \
            'data_dir' in self.opt:
            #replace model name with function 
            opt['model'] = getattr(harmonic_network_models, opt['model'])
            return
        else:
            print('ERROR: You must specify the following')
            print('\t deviceIdxs')
            print('\t dataset')
            print('\t model')
            print('\t data_dir')

    def __maybe_create(self, key, value):
        if key in self.opt:
            print('NOTE: Option [' + key + '] is specified by user. Not using default.')
            return
        else:
            self.opt[key] = value

    def __get(self, key):
        return self.opt[key]

    def __set(self, key, value):
        self.opt[key] = value

    def __data_get(self, key):
        return self.data[key]

    def __data_set(self, key, value):
        self.data[key] = value
    
    def get_options(self):
        return self.opt

    def get_data_options(self):
        return self.data

    def set_option(key, value):
        self.__set(key, value)
    
    def set_data_option(key, value):
        self.__data_set(key, value)

    def create_options(self):
        # Default configuration
        self.__maybe_create('save_step', 10)
        self.__maybe_create('trial_num', 'A')
        self.__maybe_create('lr_div', 10)
        self.__maybe_create('augment', False)
        self.__maybe_create('is_bsd', False)
        self.__maybe_create('train_data_fraction', 1.0)
        #now create options specific to datasets
        if self.__get('dataset') == 'rotated_mnist':
            self.__create_options_rotated_mnist()
        elif self.__get('dataset') == 'cifar10':
            self.__create_options_cifar10()
        elif self.__get('dataset') == 'imagenet':
            self.__create_options_imagenet_baseline()
        else:
            print('ERROR: not implemented')
            return False
        return True

    def __create_options_rotated_mnist(self):
        #setup data feeding
        mnist_dir = self.__get('data_dir') + '/mnist_rotation_new'
        #data feeding choice
        self.__set('use_io_queues', False)
        if self.__get('use_io_queues'):
            #we can use this convenience function to get all the data
            data = discover_and_setup_tfrecords(mnist_dir, 
                self.data, use_train_fraction = self.__get('train_data_fraction'))
            #define the types stored in the .tfrecords files
            self.__data_set('min_after_dequeue', 5000)
            self.__data_set('capacity', 8000)
            self.__data_set('x_type', tf.uint8)
            self.__data_set('y_type', tf.int64)
            #let's define some functions to reshape data
            #note: [] means nothing will happen
            self.__data_set('x_target_shape', [28, 28, 1, 1, 1])
            self.__data_set('y_target_shape', [1]) #a 'squeeze' is automatically applied here
            #set the data decoding function
            self.__data_set('data_decode_function', \
                (lambda features : [tf.image.convert_image_dtype(tf.image.decode_jpeg(features['x_raw']), tf.float32), \
                    tf.decode_raw(features['y_raw'], data['y_type'], name="decodeY")]))
            #set the data processing function
            self.__data_set('data_process_function', \
                (lambda x, y : [tf.image.per_image_standardization(tf.cast(x, tf.float32)), y]))
        else:
            # Download MNIST if it doesn't exist
            if not os.path.exists(self.__get('data_dir') + '/mnist_rotation_new'):
                download_dataset(self.get_options())
            # Load dataset
            mnist_dir = self.__get('data_dir') + '/mnist_rotation_new'
            train = np.load(mnist_dir + '/rotated_train.npz')
            valid = np.load(mnist_dir + '/rotated_valid.npz')
            test = np.load(mnist_dir + '/rotated_test.npz')
            self.__data_set('train_x', train['x'])
            self.__data_set('train_y', train['y'])
            self.__data_set('valid_x', valid['x'])
            self.__data_set('valid_y', valid['y'])
            self.__data_set('test_x', test['x'])
            self.__data_set('test_y', test['y'])
        self.__maybe_create('aug_crop', 0) #'crop margin'
        self.__maybe_create('n_epochs', 200)
        self.__maybe_create('batch_size', 46)
        self.__maybe_create('lr', 0.0076)
        self.__maybe_create('optimizer', tf.train.AdamOptimizer)
        self.__maybe_create('momentum', 0.93)
        self.__maybe_create('std_mult', 0.7)
        self.__maybe_create('delay', 12)
        self.__maybe_create('psi_preconditioner', 7.8)
        self.__maybe_create('filter_gain', 2)
        self.__maybe_create('filter_size', 3)
        self.__maybe_create('n_filters', 8)
        self.__maybe_create('display_step', 10000/self.__get('batch_size')*3.)
        self.__maybe_create('is_classification', True)
        self.__maybe_create('combine_train_val', False)
        self.__maybe_create('dim', 28)
        self.__maybe_create('crop_shape', 0)
        self.__maybe_create('n_channels', 1)
        self.__maybe_create('n_classes', 10)
        self.__maybe_create('log_path', './logs/deep_mnist')
        self.__maybe_create('checkpoint_path', './checkpoints/deep_mnist')
        
    def __create_options_cifar10(self):
        #setup data feeding
        mnist_dir = self.__get('data_dir') + '/cifar10'
        #data feeding choice
        self.__set('use_io_queues', False)
        if self.__get('use_io_queues'):
            #we can use this convenience function to get all the data
            data = discover_and_setup_tfrecords(mnist_dir, 
                self.data, use_train_fraction = self.__get('train_data_fraction'))
            #define the types stored in the .tfrecords files
            self.__data_set('min_after_dequeue', 5000)
            self.__data_set('capacity', 8000)
            self.__data_set('x_type', tf.uint8)
            self.__data_set('y_type', tf.int64)
            #let's define some functions to reshape data
            #note: [] means nothing will happen
            self.__data_set('x_target_shape', [32, 32, 3, 1, 1])
            self.__data_set('y_target_shape', [1]) #a 'squeeze' is automatically applied here
            #set the data decoding function
            self.__data_set('data_decode_function', \
                (lambda features : [tf.image.convert_image_dtype(tf.image.decode_jpeg(features['x_raw']), tf.float32), \
                    tf.decode_raw(features['y_raw'], data['y_type'], name="decodeY")]))
            #set the data processing function
            self.__data_set('data_process_function', \
                (lambda x, y : [tf.image.per_image_standardization(tf.cast(x, tf.float32)), y]))
        else:
            # Download CIFAR10 if it doesn't exist
            if not os.path.exists(self.__get('data_dir') + '/cifar_numpy'):
                download_dataset(self.get_options())
            # Load dataset
            self.data = load_dataset(self.__get('data_dir'), 'cifar_numpy')

        self.__maybe_create('is_classification', True)
        self.__maybe_create('dim', 32)
        self.__maybe_create('crop_shape', 0)
        self.__maybe_create('aug_crop', 3)
        self.__maybe_create('n_channels', 3)
        self.__maybe_create('n_classes', 10)
        self.__maybe_create('n_epochs', 250)
        self.__maybe_create('batch_size', 32)
        self.__maybe_create('lr', 0.01)
        self.__maybe_create('optimizer', tf.train.AdamOptimizer)
        self.__maybe_create('std_mult', 0.4)
        self.__maybe_create('delay', 8)
        self.__maybe_create('psi_preconditioner', 7.8)
        self.__maybe_create('filter_gain', 2)
        self.__maybe_create('filter_size', 3)
        self.__maybe_create('n_filters', 4*10)	# Wide ResNet
        self.__maybe_create('resnet_block_multiplicity', 3)
        self.__maybe_create('augment', True)
        self.__maybe_create('momentum', 0.93)
        self.__maybe_create('display_step', 25)
        self.__maybe_create('is_classification', True)
        self.__maybe_create('n_channels', 3)
        self.__maybe_create('n_classes', 10)
        self.__maybe_create('log_path', './logs/deep_cifar')
        self.__maybe_create('checkpoint_path', './checkpoints/deep_cifar')
        self.__maybe_create('combine_train_val', False)

    def __imagenet_data_process_function(self, x, y):
        with tf.name_scope("imagenet_data_aug") as scope:
            #random scale
            #apparently, this works better than what we have:
            #https://github.com/facebook/fb.resnet.torch
            #but let's use the 'original' formulation for now
            #randomly sample a size in specified range
            random_size = tf.squeeze(tf.random_uniform((1, 1), 256, 480, dtype=tf.int32, name="random_scale_size"))
            #rescale smaller size with this factor
            tf.cond(tf.greater(tf.shape(x)[0], tf.shape(x)[1]), 
                lambda: tf.image.resize_images(x, [tf.shape(x)[0] * (tf.shape(x)[1] / random_size), random_size]),
                lambda: tf.image.resize_images(x, [random_size, tf.shape(x)[1] * (tf.shape(x)[0] / random_size)]))
            x = tf.image.resize_images(x, [224, 224])
            #random flip
            x = tf.image.flip_left_right(x)
            #random crop
            x = tf.random_crop(x, [224, 224, 3])
            #colour augmentation
            #this is a little more involved than I first thought
            #lets pick the inception colour distortion
            #https://github.com/tensorflow/models/blob/master/inception/inception/image_processing.py
            x = tf.image.random_brightness(x, max_delta=32. / 255.)
            x = tf.image.random_saturation(x, lower=0.5, upper=1.5)
            x = tf.image.random_hue(x, max_delta=0.2)
            x = tf.image.random_contrast(x, lower=0.5, upper=1.5)
            x = tf.clip_by_value(x, 0.0, 1.0)
            #normalisation
            x = tf.image.per_image_standardization(x)
        return [x, y]

    def __create_options_imagenet_baseline(self):
        #setup data feeding
        mnist_dir = self.__get('data_dir') + '/imagenet'
        #data feeding choice
        self.__set('use_io_queues', True)
        if self.__get('use_io_queues'):
            #we can use this convenience function to get all the data
            data = discover_and_setup_tfrecords(mnist_dir, 
                self.data, use_train_fraction = self.__get('train_data_fraction'))
            #define the types stored in the .tfrecords files
            self.__data_set('min_after_dequeue', 3000)
            self.__data_set('capacity', 5000)
            self.__data_set('x_type', tf.uint8)
            self.__data_set('y_type', tf.int64)
            #let's define some functions to reshape data
            #note: [] means nothing will happen
            self.__data_set('x_target_shape', [224, 224, 3, 1, 1])
            self.__data_set('y_target_shape', [1]) #a 'squeeze' is automatically applied here
            #set the data decoding function
            self.__data_set('data_decode_function', \
                (lambda features : [tf.image.convert_image_dtype(tf.image.decode_jpeg(features['x_raw']), tf.float32), \
                    tf.decode_raw(features['y_raw'], data['y_type'], name="decodeY")]))
            #set the data processing function
            self.__data_set('data_process_function', \
                self.__imagenet_data_process_function)
        self.__maybe_create('is_classification', True)
        self.__maybe_create('dim', 224)
        self.__maybe_create('crop_shape', 0)
        self.__maybe_create('aug_crop', 3)
        self.__maybe_create('n_channels', 3)
        self.__maybe_create('n_classes', 1000)
        self.__maybe_create('n_epochs', 250)
        self.__maybe_create('batch_size', 2)
        self.__maybe_create('lr', 0.01)
        self.__maybe_create('optimizer', tf.train.MomentumOptimizer)
        self.__maybe_create('std_mult', 0.4)
        self.__maybe_create('delay', 8)
        self.__maybe_create('psi_preconditioner', 7.8)
        self.__maybe_create('filter_gain', 2)
        self.__maybe_create('filter_size', 3)
        self.__maybe_create('n_filters', 4*10)	# Wide ResNet
        self.__maybe_create('resnet_block_multiplicity', 3)
        self.__maybe_create('momentum', 0.93)
        self.__maybe_create('display_step', 25)
        self.__maybe_create('log_path', './logs/imagenet')
        self.__maybe_create('checkpoint_path', './checkpoints/imagenet')
        self.__maybe_create('combine_train_val', False)