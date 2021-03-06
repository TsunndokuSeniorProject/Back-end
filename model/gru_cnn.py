from keras.optimizers import Adam
import nltk
from nltk.corpus import stopwords
from keras.layers import LSTM, Embedding, Dense, Input, Bidirectional, GRU, Conv1D, MaxPooling1D, Flatten
from keras import Model
from gensim.models.word2vec import Word2Vec
import os
import json
from keras.preprocessing.text import Tokenizer
import csv
import numpy as np
from keras.callbacks import ModelCheckpoint
import re
from keras.preprocessing.sequence import pad_sequences
from keras.utils.np_utils import to_categorical
from file_reader import file_reader

def clean_str(string):
    string = re.sub(r"\\", "", string)
    string = re.sub(r"\'", "", string)
    string = re.sub(r"\"", "", string)
    return string.strip().lower()


MAX_SEQUENCE_LENGTH = 1000
MAX_NB_WORDS = 20000
EMBEDDING_DIM = 100
VALIDATION_SPLIT = 0.1
tokenizer = Tokenizer(num_words=25000)

train_direc = "C:/Users/USER/Downloads/test.txt"

texts = []
labels = []
sentiment = 0
# with open("../input/movie_review.csv") as csvfile:
#     reader = csv.DictReader(csvfile)
#     for row in reader:
#       texts.append(list(row.values())[4])
#       if list(row.values())[5] == 'neg':
#           labels.append(0)
#       else:
#           labels.append(1)
train_set, raw_train_labels = file_reader().read_v2(train_direc, 1, 2)
train_labels = []
for label in raw_train_labels:
    if label == -1:
        train_labels.append(2)
    else:
        train_labels.append(label)

tokenizer.fit_on_texts(train_set)

train_sequences = tokenizer.texts_to_sequences(train_set)
# train_labels = to_categorical(np.asarray(train_labels))

word_index = tokenizer.word_index
print('Number of Unique Tokens', len(word_index))

data = pad_sequences(train_sequences, maxlen=MAX_SEQUENCE_LENGTH)
print(train_labels)
labels = to_categorical(np.asarray(train_labels))
print('Shape of Data Tensor:', data.shape)
print('Shape of Label Tensor:', labels.shape)

# indices = np.arange(data.shape[0])
# np.random.shuffle(indices)
# data = data[indices]
# labels = labels[indices]

# x_train = data[:-nb_validation_samples]
# y_train = labels[:-nb_validation_samples]
# x_val = data[-nb_validation_samples:]
# y_val = labels[-nb_validation_samples:]

embeddings_index = {}
f = open('./vectors/gensim_vec.txt' ,encoding='utf8')
for line in f:
    values = line.split()
    word = values[0]
    coefs = np.asarray(values[1:], dtype='float32')
    embeddings_index[word] = coefs
f.close()

print('Total %s word vectors in provided weight direc.' % len(embeddings_index))

embedding_matrix = np.random.random((len(word_index) + 1, EMBEDDING_DIM))
for word, i in word_index.items():
    embedding_vector = embeddings_index.get(word)
    if embedding_vector is not None:
        # words not found in embedding index will be all-zeros.
        embedding_matrix[i] = embedding_vector

embeddings = Embedding(len(word_index) + 1,
                        EMBEDDING_DIM,weights=[embedding_matrix],
                        input_length=MAX_SEQUENCE_LENGTH, trainable=False)

sequence_input = Input(shape=(MAX_SEQUENCE_LENGTH,), dtype='int32')
embedded_sequences = embeddings(sequence_input)
# embedded_sequences = Embedding(len(word_index) + 1, EMBEDDING_DIM, input_length=MAX_SEQUENCE_LENGTH, trainable=True)(sequence_input)
# embedded_sequences = gensim_model.wv.get_keras_embedding()(sequence_input)
# lstm_1 = Bidirectional(LSTM(units=32, dropout=0.2, return_sequences=True))(embedded_sequences)
# lstm_last = Bidirectional(LSTM(units=32, dropout=0.2))(lstm_1)
gru = GRU(128, dropout=0.2, return_sequences=True)(embedded_sequences)
conv = Conv1D(128, 5, activation='relu')(gru)
pool = MaxPooling1D(5)(conv)
conv_2 = Conv1D(128, 5, activation='relu')(pool)
pool_2 = MaxPooling1D(5)(conv_2)
conv_3 = Conv1D(128, 5, activation='relu')(pool_2)
pool_3 = MaxPooling1D(35)(conv_3)
flat = Flatten()(pool_3)
dense = Dense(128, activation='relu')(flat)
output = Dense(3,activation='softmax')(dense)

model = Model(sequence_input, output)
model.compile(loss='categorical_crossentropy', optimizer=Adam(1e-4), metrics=['acc'])

print("Simplified LSTM neural network")
model.summary()
cp=ModelCheckpoint('model_lstm_movie2.hdf5',monitor='val_acc',verbose=1,save_best_only=True)
history=model.fit(data, labels, validation_split=VALIDATION_SPLIT, epochs=10, batch_size=32,callbacks=[cp])

# test_set = []
# test_direc = "C:/Users/USER/Desktop/574-902.txt"

# test_set, test_labels = file_reader().read_v2(path=test_direc)

# count = 0
# for l in test_labels:
#     if l==-1:
#         test_labels[count] = 0
#     count += 1

# test_sequences = tokenizer.texts_to_sequences(test_set)
# test_data = pad_sequences(test_sequences, maxlen=MAX_SEQUENCE_LENGTH)
# test_labels = to_categorical(np.asarray(test_labels))


# res = model.evaluate(test_data, test_labels)

# print(model.metrics_names)
# print(res)