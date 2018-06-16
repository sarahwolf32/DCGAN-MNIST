import tensorflow as tf
import numpy as np

'''
Generates new hand-written digit images based on the MNIST dataset.
Implementation of DCGAN.

Todo:
    Next goal: Get it working!
    - When the discriminator becomes too smart, the gradient for the discriminator goes away.
    - https://www.reddit.com/r/MachineLearning/comments/5asl74/discussion_discriminator_converging_to_0_loss_in/
    - actually train for a long time
    - if it does not work:
        - try running the tutorial code. Does that work?
    - differences b/w this and tutorial code:
        - they train the discriminator twice
        - they take random batches as samples
'''

GENERATOR_SCOPE = 'generator'
DISCRIMINATOR_SCOPE = 'discriminator'

def load_data():

    # Downloads data into ~/.keras/datasets/mnist.npz, if its not there.
    # Raw data is a tuple of np arrays ((x_train, y_train), (x_test, y_test))
    mnist = tf.keras.datasets.mnist.load_data()

    # We do not need the labels, so we will gather all examples x.
    # Return a numpy array of shape (M, 28, 28)
    x_train, x_test = mnist[0][0], mnist[1][0]
    num_train, num_test = x_train.shape[0], x_test.shape[0]
    M = num_train + num_test
    x_all = np.zeros((M, 28, 28))
    x_all[:num_train, :, :] = x_train
    x_all[num_train:, :, :] = x_test
    return x_all


def data_tensor(numpy_data):

    # Pad the images to make them 32x32, a more convenient size for this model architecture.
    x = np.zeros((numpy_data.shape[0], 32, 32))
    x[:, 2:30, 2:30] = numpy_data

    # The data is currently in a range [0, 255].
    # Transform data to have a range [-1, 1].
    # We do this to match the range of tanh, the activation on the generator's output layer.
    x = x / 128.
    x = x - 1.

    # Turn numpy array into a tensor X of shape [M, 32, 32, 1].
    X = tf.constant(x)
    X = tf.reshape(X, [-1, 32, 32, 1])
    return X

def load_dataset():
    numpy_data = load_data()
    np.random.shuffle(numpy_data)

    batch_size = 128
    num_batches = int(np.ceil(numpy_data.shape[0] / float(batch_size)))

    X = data_tensor(numpy_data)
    dataset = tf.data.Dataset.from_tensor_slices(X)
    dataset = dataset.batch(batch_size)
    return dataset, num_batches


def generator(Z, initializer):
    '''
    Takes an argument Z, a [M, 100] tensor of random numbers.
    Returns an operation that creates a generated image of shape [None, 32, 32, 1]
    '''

    with tf.variable_scope(GENERATOR_SCOPE):

        # Input Layer
        input_fc = tf.layers.dense(Z, 4*4*256, kernel_initializer=initializer, name='input')
        input_norm = tf.layers.batch_normalization(input_fc)
        input_relu = tf.nn.relu(input_norm)
        input_reshape = tf.reshape(input_relu, [-1, 4, 4, 256])

        # Layer 1
        deconv_1 = tf.layers.conv2d_transpose(
            input_reshape, 
            filters=32, 
            kernel_size=[5,5], 
            strides=[2,2], 
            padding='SAME',
            kernel_initializer=initializer, 
            name='layer1')
        norm_1 = tf.layers.batch_normalization(deconv_1)
        relu_1 = tf.nn.relu(norm_1)

        # Layer 2
        deconv_2 = tf.layers.conv2d_transpose(
            relu_1, 
            filters=32, 
            kernel_size=[5,5], 
            strides=[2,2], 
            padding='SAME', 
            kernel_initializer=initializer,
            name='layer2')
        norm_2 = tf.layers.batch_normalization(deconv_2)
        relu_2 = tf.nn.relu(norm_2)

        # Layer 3
        deconv_3 = tf.layers.conv2d_transpose(
            relu_2,
            filters=16, 
            kernel_size=[5,5], 
            strides=[2,2], 
            padding='SAME', 
            kernel_initializer=initializer,
            name='layer3')
        norm_3 = tf.layers.batch_normalization(deconv_3)
        relu_3 = tf.nn.relu(norm_3)

        # Output Layer
        output = tf.layers.conv2d_transpose(
            relu_3, 
            filters=1,
            kernel_size=[32,32],
            padding='SAME',
            activation=tf.nn.tanh,
            kernel_initializer=initializer,
            name='output')

        # Generated images of shape [M, 32, 32, 1]
        return output


# Discriminator
def discriminator(images, initializer, reuse):
    '''
    Takes an image as an argument [None, 32, 32, 1].
    Returns an operation that gives the probability of that image being 'real' [None, 1]
    '''

    with tf.variable_scope(DISCRIMINATOR_SCOPE, reuse=reuse):

        # Layer 1 => [M, 16, 16, 16]
        conv_1 = tf.layers.conv2d(
            images, 
            filters=16, 
            kernel_size=[4,4], 
            strides=[2,2], 
            padding='SAME', 
            activation=tf.nn.leaky_relu,
            kernel_initializer=initializer, 
            name='layer1')

        # Layer 2 => [M, 8, 8, 32]
        conv_2 = tf.layers.conv2d(
            conv_1, 
            filters=32, 
            kernel_size=[4,4], 
            strides=[2,2], 
            padding='SAME', 
            kernel_initializer=initializer,
            name='layer2')
        norm_2 = tf.layers.batch_normalization(conv_2)
        lrelu_2 = tf.nn.leaky_relu(norm_2)

        # Layer 3 => [M, 4, 4, 64]
        conv_3 = tf.layers.conv2d(
            lrelu_2, 
            filters=64, 
            kernel_size=[4,4], 
            strides=[2,2], 
            padding='SAME', 
            kernel_initializer=initializer, 
            name='layer3')
        norm_3 = tf.layers.batch_normalization(conv_3)
        lrelu_3 = tf.nn.leaky_relu(norm_3)

        # Output layer
        output_flat = tf.layers.flatten(lrelu_3) # => [M, 4*4*64]
        output_fc = tf.layers.dense(
            output_flat, 
            units=1, 
            kernel_initializer=initializer, 
            name='output') 
        output_norm = tf.layers.batch_normalization(output_fc)
        output = tf.nn.sigmoid(output_norm)  # => [M, 1]

        return output

# loss
def loss(Dx, Dg):
    '''
    Dx = Probabilities assigned by D to the real images, [M, 1]
    Dg = Probabilities assigned by D to the generated images, [M, 1]
    '''
    with tf.variable_scope('loss'):
        loss_d = -tf.reduce_mean(tf.log(Dx) + tf.log(1. - Dg))
        #loss_g = tf.reduce_mean(tf.log(1. - Dg))
        loss_g = -tf.reduce_mean(tf.log(Dg))
        return loss_d, loss_g


# Training
def trainers(images_holder, Z_holder):

    # forward pass
    weights_initializer = tf.truncated_normal_initializer(stddev=0.02)
    generated_images = generator(Z_holder, weights_initializer)
    Dx = discriminator(images_holder, weights_initializer, False)
    Dg = discriminator(generated_images, weights_initializer, True)

    # compute losses
    loss_d, loss_g = loss(Dx, Dg)

    # optimizers
    optimizer_g = tf.train.AdamOptimizer(learning_rate=0.0002, beta1=0.5)
    optimizer_d = tf.train.AdamOptimizer(learning_rate=0.0002, beta1=0.5)

    # backprop
    g_vars = tf.trainable_variables(scope=GENERATOR_SCOPE)
    d_vars = tf.trainable_variables(scope=DISCRIMINATOR_SCOPE)
    train_g = optimizer_g.minimize(loss_g, var_list=g_vars)
    train_d = optimizer_d.minimize(loss_d, var_list = d_vars)

    return train_d, train_g, loss_d, loss_g, generated_images


# Main

# create a placeholders
images_holder = tf.placeholder(tf.float32, shape=[None, 32, 32, 1])
Z_holder = tf.placeholder(tf.float32, shape=[None, 100])

# get trainers
train_d, train_g, loss_d, loss_g, generated_images = trainers(images_holder, Z_holder)
init = tf.global_variables_initializer()

# prepare summaries
loss_d_summary_op = tf.summary.scalar('Discriminator Loss', loss_d)
loss_g_summary_op = tf.summary.scalar('Generator Loss', loss_g)
images_summary_op = tf.summary.image('Generated Image', generated_images, max_outputs=1)
training_images_summary_op = tf.summary.image('Training Image', images_holder, max_outputs=1)
summary_op = tf.summary.merge_all()
writer = tf.summary.FileWriter('dcgan_summaries', graph=tf.get_default_graph())

with tf.Session() as sess:
    sess.run(init)

    # dataset
    dataset, num_batches = load_dataset()
    iterator = dataset.make_initializable_iterator()
    next_batch = iterator.get_next()

    # loop over epochs
    num_epochs = 2000
    global_step = 0
    min_discriminator_loss = 0.5

    for epoch in range(num_epochs):
        sess.run(iterator.initializer)
        print("epoch: " + str(epoch))

        # loop over batches
        for i in range(num_batches):

            # train
            images = sess.run(next_batch)
            Z = np.random.uniform(-1.0, 1.0, size=[images.shape[0], 100])
            print("batch " + str(i) + ": images_shape = " + str(images.shape) + ", Z_shape = " + str(Z.shape))

            # run session
            feed_dict = {images_holder: images, Z_holder: Z}
            loss_d_val = sess.run(loss_d, feed_dict=feed_dict)
            if loss_d_val > min_discriminator_loss:
                sess.run(train_d, feed_dict=feed_dict)
            _, loss_g_val = sess.run([train_g, loss_g], feed_dict=feed_dict)
            #_, loss_g_val = sess.run([train_g, loss_g], feed_dict=feed_dict) # update the generator twice! 

            # tensorboard
            if global_step % 10 == 0:
                summary = sess.run(summary_op, feed_dict=feed_dict)
                writer.add_summary(summary, global_step=global_step)
            global_step += 1

            # print losses
            print("G loss: " + str(loss_g_val))
            print("D loss: " + str(loss_d_val))
            








# Temporary Tests
""" # Test generator
    # create a [M, 100] constant
    # run it through the generator
    # output should be correct shape
print ("testing generator!")
M = 5
Z = tf.random_uniform([M, 100])
G = generator(Z, weights_initializer)
init = tf.global_variables_initializer()
sess = tf.Session()
sess.run(init)
out = sess.run(G)
print("got an out for G!")
print("should be of shape [M, 32, 32, 1]")
print("real shape: " + str(out.shape)) 


# Test discriminator
    # create a [M, 32, 32, 1] constant
    # run it through the discriminator
    # output should be of the correct shape
print("testing discriminator!")
M = 5
images = tf.random_uniform([M, 32, 32, 1])
D = discriminator(images, weights_initializer)
init = tf.global_variables_initializer()
with tf.Session() as sess:
    sess.run(init)
    out = sess.run(D)
    print("got an out! Should be shape [M, 1]")
    print("out.shape:")
    print(out.shape)
    print(out) 

# Test loss
    # create two [M, 1] constants
    # evaluate losses
    # should get back two floats
print("testing loss!")
Dx = tf.random_uniform([M, 1])
Dg = tf.random_uniform([M, 1])
with tf.Session() as sess:
    loss_d, loss_g = sess.run(loss(Dx, Dg))
    print("loss_d = ", str(loss_d))
    print("loss_g = ", str(loss_g)) """


""" 
print("done loading data!")

sess = tf.Session()

d = sess.run(X)
print("data shape:")
print(d.shape) 
"""