import math
import random
import numpy
import tensorflow as tf
from tensorflow import keras

ratio = 0.75
data = [math.sin(n) * 100 + random.random() * 10 * random.choice([-1, 1]) for n in range(10001)]
l=[]
xs = []
ys = []
for i in range(0, 10000, 20):
    for j in range(i, i + 20):
        l.append(data[j])
    xs.append(l)
    ys.append(data[i + 20])
    l = []

master = [(xs[i], ys[i]) for i in range(len(xs))]
random.shuffle(master)
train = master[:int(len(master) * ratio)]
train_xs = numpy.array([train[i][0] for i in range(len(train))])
train_ys = numpy.array([train[i][1] for i in range(len(train))])
val = master[int(len(master) * ratio):]
val_xs =numpy.array([val[i][0] for i in range(len(val))])
val_ys = numpy.array([val[i][1] for i in range(len(val))])
print(train[0])
print(train_xs[0])
print(train_ys[0])

model = keras.models.Sequential([
  keras.layers.Lambda(lambda x: tf.expand_dims(x, axis=-1), input_shape=(20,)),
  keras.layers.Bidirectional(keras.layers.LSTM(32, return_sequences=True)),
  keras.layers.Bidirectional(keras.layers.LSTM(16)),
  keras.layers.Dense(units=32, activation='relu'),
  keras.layers.Dense(units=16, activation='relu'),
  keras.layers.Dense(1)
])

model.compile(optimizer='sgd', loss='huber', metrics=['acc'])
print(model.summary())
model.fit(x=train_xs, y=train_ys, epochs=500, validation_data=(val_xs, val_ys))



