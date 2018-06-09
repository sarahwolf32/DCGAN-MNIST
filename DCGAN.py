import tensorflow as tf
import numpy as np

'''
Generates new hand-written digit images based on the MNIST dataset.
Implementation of DCGAN.

Issues:
    - Tutorial seems to expect MNIST images to be 32x32, but I think they are 28x28.
'''

# Load data
'''
Downloads data into ~/.keras/datasets/mnist.npz, if its not there.
Returns a tuple of np arrays ((x_train, y_train), (x_test, y_test))
We do not need the labels, so we will gather all examples x.
'''
mnist = tf.keras.datasets.mnist.load_data()
x_train = mnist[0][0] # [60000, 28, 28]
x_test = mnist[1][0] # [10000, 28, 28]
x = np.zeros((70000, 28, 28))
x[0:60000, :, :] = x_train
x[60000:, :, :] = x_test


# Pre-processing
'''
The data is currently in a range [0, 255].
Transform data to have a range [-1, 1].
We do this to match the range of tanh, the activation on the generator's output layer.
'''
x = x / 128.
x = x - 1.


# Setup
'''
We now have a numpy array of shape (70000, 28, 28). 
Turn it into a tensor X.
'''
X = tf.constant(x)


# Generator
'''
Takes z as an argument, a 100-length vector.
Returns an operation that creates an image of shape [None, 32, 32, 1]

Input FC
    4 * 4 * 256, batch norm, ReLU
    Reshape - [None, 4, 4, 256]

Deconv1 
    32 filters
    kernal_size = [5,5]
    stride = [2,2]
    padding = 'SAME'
    Batch Norm
    ReLU

Deconv2
    32 filters
    kernal_size = [5,5]
    stride = [2,2]
    padding = 'SAME'
    Batch Norm
    ReLU

Deconv3
    16 filters
    kernal_size = [5,5]
    stride = [2,2]
    padding = 'SAME'
    Batch Norm
    ReLU

Output
    1 filter
    kernal_size = [32, 32]
    padding = 'SAME'
    Tanh
'''

# Discriminator
'''
Takes an image as an argument [None, 32, 32, 1].
Returns an operation that gives the probability of that image being 'real' [None, 1]

Conv1
    16 filters
    kernal_size = [4, 4]
    stride = [2, 2]
    padding = 'SAME'
    LeakyReLU, slope = 0.2

Conv2
    32 filters
    kernal_size = [4, 4]
    stride = [2, 2]
    padding = 'SAME'
    Batch Norm
    LeakyReLU, slope = 0.2

Conv3
    64 filters
    kernal_size = [4, 4]
    stride = [2, 2]
    padding = 'SAME'
    Batch Norm
    LeakyReLU, slope = 0.2

Output
    Flatten
    FC - 1 node
    Sigmoid

'''

# Training
'''
Loss(D) = -(1/m) SUM_OVER_M[ log(D(x)) + log(1 - D(G(z)))]
Loss(G) = (1/m) SUM_OVER_M[ log(1 - D(G(z)))]

Mini-batch size 128
Mini-batch stochastic gradient descent
Initialize weights from zero-centered normal distribution, 0.02 standard deviation
AdamOptimizer => learning_rate = 0.0002, B1 = 0.5
'''