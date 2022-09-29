import pickle
import matplotlib.pyplot as plt
import numpy
import tensorflow as tf

with open('TSLA/data.txt', 'rb') as file:
    data = list(dict(dict(pickle.load(file))['Open']).values())

#plt.plot(data)
#plt.show()

xs = []
ys = []
index = 0
while index + 20 < len(data):
    xs.append(data[index:index+20])
    ys.append(data[index + 20])
    index += 1

xs = numpy.array(xs)
ys = numpy.array(ys)
print(xs[4])
print(ys[4])
print(xs.shape)
print(ys.shape)

model = tf.keras.models.Sequential([
  # tf.keras.layers.Conv1D(filters=64, kernel_size=3,
  #                     strides=1,
  #                     activation="relu",
  #                     padding='causal',
  #                     input_shape=[20, 1]),
  # tf.keras.layers.LSTM(64, return_sequences=True),
  # tf.keras.layers.LSTM(64),
    tf.keras.layers.Dense(20, activation="relu", input_shape=(20,)),
    tf.keras.layers.Dense(10, activation="relu"),
    tf.keras.layers.Dense(4, activation='relu'),
    tf.keras.layers.Dense(1)
])


model.summary()
model.compile(loss='huber', optimizer='sgd', metrics=['acc'])
model.fit(
    x=xs, y=ys, epochs=100, verbose=1
)

model.save('TSLA/model.h5')
