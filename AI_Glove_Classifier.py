import serial
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from tensorflow.python.saved_model import saved_model

import tensorflow as tf
from tensorflow.keras.models import Sequential, save_model, load_model

# ser = serial.Serial('COM6', 19200)
# ser.flushInput()

NUM_SAMPLES = 70
count = 0
inputs = []
tensor = []

filename = "wrist_pain_hammer.csv"

df = pd.read_csv(filename)

index = range(1, len(df['y']) + 1)

plt.rcParams["figure.figsize"] = (20,10)

plt.plot(index, df['y'], 'g.', label='y', linestyle='solid', marker=',')
plt.plot(index, df['p'], 'b.', label='p', linestyle='solid', marker=',')
plt.plot(index, df['r'], 'r.', label='r', linestyle='solid', marker=',')
plt.plot(index, df['flex1'], 'g.', label='f1', linestyle='solid', marker=',')
plt.plot(index, df['flex2'], 'b.', label='f2', linestyle='solid', marker=',')
plt.plot(index, df['flex3'], 'r.', label='f3', linestyle='solid', marker=',')
plt.plot(index, df['flex4'], 'r.', label='f4', linestyle='solid', marker=',')
plt.title("Position")
plt.xlabel("Sample #")
plt.ylabel("Position (Data)")
plt.legend()
plt.show()

# Set a fixed random seed value, for reproducibility, this will allow us to get
# the same random numbers each time the notebook is run
SEED = 1337
np.random.seed(SEED)
tf.random.set_seed(SEED)

# the list of gestures that data is available for
GESTURES = [
    "wrist_extension", "wrist_flexion", "ulnar_nerve_glide", "ulnar_nerve_glide2", "tendon_glide", "wrist_pain_hammer"
]

SAMPLES_PER_GESTURE = 70

NUM_GESTURES = len(GESTURES)

# create a one-hot encoded matrix that is used in the output
ONE_HOT_ENCODED_GESTURES = np.eye(NUM_GESTURES)

inputs = []
outputs = []

# read each csv file and push an input and output
for gesture_index in range(NUM_GESTURES):
    gesture = GESTURES[gesture_index]
    print(f"Processing index {gesture_index} for gesture '{gesture}'.")

    output = ONE_HOT_ENCODED_GESTURES[gesture_index]

    df = pd.read_csv(gesture + ".csv")

    # calculate the number of gesture recordings in the file
    num_recordings = int(df.shape[0] / SAMPLES_PER_GESTURE)

    print(f"\tThere are {num_recordings} recordings of the {gesture} gesture.")

    for i in range(num_recordings):
        tensor = []
        for j in range(SAMPLES_PER_GESTURE):
            index = i * SAMPLES_PER_GESTURE + j
            # normalize the input data, between 0 to 1:
            # - acceleration is between: -4 to +4
            # - gyroscope is between: -2000 to +2000
            tensor += [
                (df['y'][index] + 180) / 360,
                (df['p'][index] + 180) / 360,
                (df['r'][index] + 180) / 360,
                (df['flex1'][index] + 0) / 2046,
                (df['flex2'][index] + 0) / 2046,
                (df['flex3'][index] + 0) / 2046,
                (df['flex4'][index] + 0) / 2046,
            ]
            # print(tensor)

        inputs.append(tensor)
        outputs.append(output)

# convert the list to numpy array
# print(inputs[0])
inputs = np.array(inputs)
print(inputs[0].size)
outputs = np.array(outputs)

print("Data set parsing and preparation complete.")

# Randomize the order of the inputs, so they can be evenly distributed for training, testing, and validation
# https://stackoverflow.com/a/37710486/2020087
num_inputs = len(inputs)
randomize = np.arange(num_inputs)
np.random.shuffle(randomize)

# Swap the consecutive indexes (0, 1, 2, etc) with the randomized indexes
inputs = inputs[randomize]
outputs = outputs[randomize]

# Split the recordings (group of samples) into three sets: training, testing and validation
TRAIN_SPLIT = int(0.6 * num_inputs)
TEST_SPLIT = int(0.2 * num_inputs + TRAIN_SPLIT)

inputs_train, inputs_test, inputs_validate = np.split(inputs, [TRAIN_SPLIT, TEST_SPLIT])
outputs_train, outputs_test, outputs_validate = np.split(outputs, [TRAIN_SPLIT, TEST_SPLIT])

print("Data set randomization and splitting complete.")
print(inputs_test[0].size)
#
# build the model and train it
model = tf.keras.Sequential()
model.add(tf.keras.layers.Dense(50, activation='relu')) # relu is used for performance
model.add(tf.keras.layers.Dense(15, activation='relu'))
model.add(tf.keras.layers.Dense(NUM_GESTURES, activation='softmax')) # softmax is used, because we only expect one gesture to occur per input
model.compile(optimizer='rmsprop', loss='mse', metrics=['mae'])
history = model.fit(inputs_train, outputs_train, epochs=600, batch_size=1, validation_data=(inputs_validate, outputs_validate))

model.save("mymodel")

# increase the size of the graphs. The default size is (6,4).
plt.rcParams["figure.figsize"] = (20,10)

# graph the loss, the model above is configure to use "mean squared error" as the loss function
loss = history.history['loss']
val_loss = history.history['val_loss']
epochs = range(1, len(loss) + 1)
plt.plot(epochs, loss, 'g.', label='Training loss')
plt.plot(epochs, val_loss, 'b', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

print(plt.rcParams["figure.figsize"])

# graph the loss again skipping a bit of the start
SKIP = 100
plt.plot(epochs[SKIP:], loss[SKIP:], 'g.', label='Training loss')
plt.plot(epochs[SKIP:], val_loss[SKIP:], 'b.', label='Validation loss')
plt.title('Training and validation loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.legend()
plt.show()

# graph of mean absolute error
mae = history.history['mae']
val_mae = history.history['val_mae']
plt.plot(epochs[SKIP:], mae[SKIP:], 'g.', label='Training MAE')
plt.plot(epochs[SKIP:], val_mae[SKIP:], 'b.', label='Validation MAE')
plt.title('Training and validation mean absolute error')
plt.xlabel('Epochs')
plt.ylabel('MAE')
plt.legend()
plt.show()

# use the model to predict the test inputs
predictions = model.predict(inputs_test)

# print the predictions and the expected ouputs
print("predictions =\n", np.round(predictions, decimals=3))
print("actual =\n", outputs_test)

# Plot the predictions along with to the test data
plt.clf()
plt.title('Training data predicted vs actual values')
plt.plot(inputs_test, outputs_test, 'b.', label='Actual')
plt.plot(inputs_test, predictions, 'r.', label='Predicted')
plt.show()
# #
# # tf.keras.model.save('saved_model/my_model')
# # actual = []
# # tensor = []
# # arr = []
# #
# # while True:
# #     try:
# #         input = ser.readline().decode('utf-8').strip()
# #         input = input.split(",")
# #         y = input[0]
# #         p = input[1]
# #         r = input[2]
# #         print(y, p, r)
# #         if count < NUM_SAMPLES:
# #             actual.append((float(y) + 180) / 360)
# #             actual.append((float(p) + 180) / 360)
# #             actual.append((float(r) + 180) / 360)
# #             count+=1
# #         else: #run classifier
# #             arr.append(actual)
# #             arr = np.array(arr)
# #             print(arr)
# #             predictions = model.predict(arr)
# #             print("predictions =\n", np.round(predictions, decimals=3))
# #             count = 0
# #             actual=[]
# #             arr=[]
# #     except:
# #         pass