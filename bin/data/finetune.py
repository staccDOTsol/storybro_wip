import os
import tarfile

import tensorflow as tf
import tensorflow_datasets as tfds

import gpt_2_simple as gpt2

model_name = "1558M"
if not os.path.isdir(os.path.join("models", model_name)):
    print("Downloading ", model_name, " model...")
    gpt2.download_gpt2(
        model_name=model_name
    )  # model is saved into current directory under /models/124M/

file_name = "text_adventures.txt"
resolver = tf.tpu.cluster_resolver.TPUClusterResolver(tpu="grpc://10.91.76.114:8470")
tf.tpu.distribute.initialize_tpu_system(resolver)
strategy = tf.tpu.distribute.TPUStrategy(resolver)
with strategy.scope():
    sess = gpt2.start_tf_sess(server=resolver)
    gpt2.finetune(
        sess,
        file_name,
        multi_gpu=True,
        batch_size=8,
        learning_rate=0.0001,
        model_name=model_name,
        sample_every=10000,
        max_checkpoints=8,
        save_every=1000,
        steps=5000,
    )

gpt2.generate(sess)
