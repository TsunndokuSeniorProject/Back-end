import numpy as np
import pandas as pd
import pickle
from collections import defaultdict
import re
import csv
import sys
import json
import os
from keras.preprocessing.text import Tokenizer
from keras.preprocessing.sequence import pad_sequences
from keras.utils.np_utils import to_categorical
from keras.layers import Embedding
from keras.layers import Dense, Input, Flatten
from keras.layers import Conv1D, MaxPooling1D, Embedding, Dropout, BatchNormalization, Activation
from keras.models import Model
from keras.optimizers import Adam
from keras.callbacks import ModelCheckpoint
import matplotlib.pyplot as plt
plt.switch_backend('agg')

def clean_str(string):
    string = re.sub(r"\\", "", string)
    string = re.sub(r"\'", "", string)
    string = re.sub(r"\"", "", string)
    return string.strip().lower()


MAX_SEQUENCE_LENGTH = 1000
MAX_NB_WORDS = 20000
EMBEDDING_DIM = 100
VALIDATION_SPLIT = 0.2


directory = "C:/Users/USER/Desktop/sentiment/sentiment-analysis-on-movie-reviews/"
texts = []
labels = []
with open(directory+'train.tsv') as tsvfile:
  reader = csv.DictReader(tsvfile, dialect='excel-tab')
  for row in reader:
    texts.append(list(row.values())[2])
    labels.append(list(row.values())[3])

# for file in os.listdir(romance_direc):
#     with open(romance_direc+file, 'r') as fp:
#         data = json.load(fp)
#         for comment in data['Reviews']:
#             texts.append(clean_str(comment['Review']))
#         fp.close()

tokenizer = Tokenizer(num_words=MAX_NB_WORDS)
tokenizer.fit_on_texts(texts)
sequences = tokenizer.texts_to_sequences(texts)

word_index = tokenizer.word_index
print('Number of Unique Tokens', len(word_index))

data = pad_sequences(sequences, maxlen=MAX_SEQUENCE_LENGTH)
labels = to_categorical(np.asarray(labels))
print('Shape of Data Tensor:', data.shape)
print('Shape of Label Tensor:', labels.shape)

indices = np.arange(data.shape[0])
np.random.shuffle(indices)
data = data[indices]
labels = labels[indices]
nb_validation_samples = int(VALIDATION_SPLIT * data.shape[0])

x_train = data[:-nb_validation_samples]
y_train = labels[:-nb_validation_samples]
x_val = data[-nb_validation_samples:]
y_val = labels[-nb_validation_samples:]

embeddings_index = {}
f = open('C:/Users/USER/Downloads/glove.6B/glove.6B.100d.txt',encoding='utf8')
for line in f:
    values = line.split()
    word = values[0]
    coefs = np.asarray(values[1:], dtype='float32')
    embeddings_index[word] = coefs
f.close()

print('Total %s word vectors in Glove 6B 100d.' % len(embeddings_index))

# embedding_matrix = np.random.random((len(word_index) + 1, EMBEDDING_DIM))
# for word, i in word_index.items():
#     embedding_vector = embeddings_index.get(word)
#     if embedding_vector is not None:
#         # words not found in embedding index will be all-zeros.
#         embedding_matrix[i] = embedding_vector

# embedding_layer = Embedding(len(word_index) + 1,
#                             EMBEDDING_DIM,weights=[embedding_matrix],
#                             input_length=MAX_SEQUENCE_LENGTH,trainable=True)


sequence_input = Input(shape=(MAX_SEQUENCE_LENGTH,), dtype='int32')
# embedded_sequences = embedding_layer(sequence_input)
embedding = Embedding(len(word_index) + 1, EMBEDDING_DIM, input_length=MAX_SEQUENCE_LENGTH, trainable=True)(sequence_input)
cov1= Conv1D(96, 5, activation='relu')(embedding)
bn = BatchNormalization()(cov1)
pool1 = MaxPooling1D(5)(bn)
cov2 = Conv1D(256, 5, activation='relu')(pool1)
bn2 = BatchNormalization()(cov2)
pool2 = MaxPooling1D(5)(bn2)
cov3 = Conv1D(384, 5, activation='relu')(pool2)
# cov4 = Conv1D(128, 5, activation='relu')(cov3)
bn3 = BatchNormalization()(cov3)
pool3 = MaxPooling1D(35)(bn3)  # global max pooling
flat = Flatten()(pool3)
dense = Dense(128, activation='relu')(flat)
output = Dense(5, activation='softmax')(dense)

model = Model(sequence_input, output)
model.compile(loss='categorical_crossentropy',
              optimizer=Adam(),
              metrics=['acc'])

print("Simplified convolutional neural network")
model.summary()
cp=ModelCheckpoint('model_cnn.hdf5',monitor='val_acc',verbose=1,save_best_only=True)
history=model.fit(x_train, y_train, validation_data=(x_val, y_val), epochs=7, batch_size=32,callbacks=[cp])