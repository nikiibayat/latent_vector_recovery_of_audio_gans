import numpy as np
import tensorflow as tf

import random
import os
import time
import glob
from scipy.io import wavfile
from PIL import Image
from tensorflow.python.keras.utils.data_utils import Sequence

tf.disable_eager_execution()
os.environ["CUDA_VISIBLE_DEVICES"] = str(1)

BATCH_SIZE = 50


tf.reset_default_graph()
saver = tf.train.import_meta_graph('infer.meta')
graph = tf.get_default_graph()
sess = tf.InteractiveSession()
saver.restore(sess, 'model.ckpt')


def convert_to_spectogram(audio):
    audio = tf.squeeze(audio)
    audio = tf.signal.stft(audio, 256, 128, pad_end=True)
    audio = tf.expand_dims(audio, -1)

    audio = tf.stack([
        audio,
        audio,
        audio
    ], axis=-1)

    audio = tf.squeeze(audio)
    audio = tf.cast(audio, tf.float32)
    return audio


def generate_fake_audio():
    # Create 50 random latent vectors z
    _z = (np.random.rand(BATCH_SIZE, 100) * 2.) - 1
    # Synthesize G(z)
    z = graph.get_tensor_by_name('z:0')
    G_z = graph.get_tensor_by_name('G_z:0')
    _G_z = sess.run(G_z, {z: _z})

    for x in range(0, BATCH_SIZE):
        spectogram = convert_to_spectogram(_G_z[x])
        spectogram = sess.run(spectogram)
        spectogram = (spectogram * 255.).astype(np.uint8)
        print("Spectogram shape: ", spectogram.shape)
        # Image.fromarray(spectogram).save("fake_audio/wavegan_digit/"+"audio_"+str(x)+".png")
        # wavfile.write("fake_audio/wavegan_digit/"+"audio_"+str(x)+".wav", 16384, _G_z[x])


train_path = glob.glob("/home/nbayat5/wavegan_inverse_mapping/fake_audio/wavegan_digit/*.wav")


def train_generator(train_path):
    for x in range(0, len(train_path)):
        path = train_path[x]
        path_label = path.split("/")[-1].split(".")[0]
        sr, audio = wavfile.read(path)
        audio = audio.astype(np.float32)
        audio = audio / 32767
        audio = audio * 1.414
        audio = librosa.core.resample(audio, 16000, 16384)
        audio = audio[0:16384]
        data = np.zeros(16384)
        data[0:audio.shape[0]] = audio

    yield path_label, data


def recover_latent_vector():
    dataset = tf.data.Dataset.from_generator(train_generator, output_types=(tf.string, tf.float32)).batch(1)
    print("Number of audio: ", len(train_path))
    num_iters = 200
    z_vectors = []

    for batch, (label, audio) in enumerate(dataset):
        print("Batch: ", batch)
        audio = tf.Variable(convert_to_spectogram(audio),validate_shape=False)
        print("Audio shape: ", audio.shape)

        # _z = tf.Variable((np.random.rand(1, 100) * 2.) - 1, tf.float32,validate_shape=False)
        # z = graph.get_tensor_by_name('z:0')
        # G_z = graph.get_tensor_by_name('G_z:0')
        # _G_z = sess.run(G_z, {z: _z})
        #
        # predicted_spectogram = convert_to_spectogram(G_z)
        #
        # loss = tf.keras.losses.MeanAbsoluteError()(audio, predicted_spectogram)
        #
        # global_step = tf.Variable(0, trainable=False)
        # learning_rate = tf.constant(0.01)
        # opt = tf.train.AdamOptimizer(learning_rate)
        # train = opt.minimize(loss, var_list=_z, global_step=global_step)
        #
        # start_time = time.time()
        # for i in range(num_iters):
        #     print("step: ", i + 1)
        #     _, loss_value, zp_val, eta = sess.run((train, loss, _z, learning_rate))
        #
        #     """Uncomment below lines if you want to add stochastic clipping"""
        #     # stochastic clipping
        #     # zp_val[zp_val > 1] = random.uniform(-1, 1)
        #     # zp_val[zp_val < -1] = random.uniform(-1, 1)
        #
        # print("-" * 50)
        # print("Time for one batch:  %s seconds" % (time.time() - start_time))
        # print("-" * 50)
        #
        # zp_val = sess.run(_z)
        # z_vectors.append(zp_val)
        #
        # recovered_audio = sess.run(G_z, {z: _z})
        # wavfile.write("recovered_audio/wavegan_digit/" + "audio_" + str(batch) + ".wav", 16384, recovered_audio[0])
        break

if __name__ == "__main__":
    # generate_fake_audio()
    recover_latent_vector()