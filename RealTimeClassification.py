import serial
import tensorflow as tf
from matplotlib.ticker import NullFormatter  # useful for `logit` scale
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import PySimpleGUI as sg
import matplotlib
matplotlib.use('TkAgg')
import time
import random
from PIL import Image, ImageTk, ImageSequence
matplotlib.use('TkAgg')

ser = serial.Serial('COM9 ', 19200)
ser.flushInput()

# Variables for classification
model = tf.keras.models.load_model("mymodel")
GESTURES = ["wrist_extension", "wrist_flexion", "ulnar_nerve_glide", "ulnar_nerve_glide2", "tendon_glide", "wrist_pain_hammer"]
NUM_SAMPLES = 70

def read_gesture():
    counter = 0
    j = 0
    actual = []
    arr = []
    inputs = []
    while True:
        try:
            if counter < NUM_SAMPLES:
                ser.flushInput()
                inputs = ser.readline().decode('utf-8').strip()
                inputs = inputs.split()
                y_raw = inputs[0]
                p_raw = inputs[1]
                r_raw = inputs[2]
                flex1 = inputs[3]
                flex2 = inputs[4]
                flex3 = inputs[5]
                flex4 = inputs[6]
                print(y_raw, p_raw, r_raw, flex1, flex2, flex3, flex4)
                # arr.append(j)
                actual.append((float(y_raw) + 180) / 360)
                actual.append((float(p_raw) + 180) / 360)
                actual.append((float(r_raw) + 180) / 360)
                actual.append((float(flex1) + 0) / 2046)
                actual.append((float(flex2) + 0) / 2046)
                actual.append((float(flex3) + 0) / 2046)
                actual.append((float(flex4) + 0) / 2046)
                counter+=1
                # j+=1

            else: #run classifier
                print(len(actual))
                arr.append(actual)
                arr = np.array(arr)
                # print(arr[0])
                predictions = model.predict(arr)
                print("predictions =\n", np.round(predictions, decimals=3))
                print("gesture:", GESTURES[np.argmax(predictions[0])])
                counter = 0
                actual=[]
                arr=[]
                return GESTURES[np.argmax(predictions[0])]
        except:
            print("except:", inputs)
            pass
display_width = 800
display_height = 600
failed_gestures = []
correct_gestures = []
for i in range(len(GESTURES)):
    correct_gestures.append(0)
print(correct_gestures)
sg.theme('DarkAmber')
# Define the window's contents
menu_layout = [[sg.Text("Helping Hand",justification='center',font='Helvetica 25', text_color='yellow')],
          [sg.Button('Streak Mode', size=(15, 2))],
          [sg.Button('Memory Mode', size=(15, 2))],
          [sg.Button('Practice Mode', size=(15, 2))],
          [sg.Button('Stats', size=(15, 2))],
               [sg.Canvas(key='graph1')]]
streak_layout = [[sg.Text("Streak",font='Helvetica 25', text_color='yellow'), sg.Text(size=(40,1), font='Helvetica 18', text_color='red', key='streak_count')],
                 [sg.Text(size=(40,1),font='Helvetica 18', text_color='yellow',key='gesture_name')],
                 [sg.Image(key='gif')],
                 [sg.Button('Start Streak', size=(10, 2))],
                 [sg.Text(font='Helvetica 16',size=(40,1),text_color='white', key='-OUTPUT1-')],
                 [sg.Text(font='Helvetica 16',size=(40,1), text_color='white', key='-OUTPUT2-')]]
results_layout = [[sg.Text("Streak Ended! Results: ",font='Helvetica 25', text_color='yellow'), sg.Text(size=(40,1), font='Helvetica 18', text_color='red', key='streak_result')],
                 [sg.Text("Highscore: ",font='Helvetica 25', text_color='yellow'),sg.Text(size=(40,1), font='Helvetica 18', text_color='red', key='highscore')],
                 *[[sg.Text(f'{i}', key=f'{i}')] for i in GESTURES],
                 [sg.Button('History', size=(10, 2))],
                  [sg.Canvas(key='graph2')]]

recommend_layout = [[sg.Text("Based on your recent performance, we recommend the following exercises: ",font='Helvetica 25')],
                 [sg.Text(size=(40,1), font='Helvetica 18', text_color='red', key='recommend')]]

layout = [[sg.Column(menu_layout, element_justification='center', key='menu_layout'), sg.Column(streak_layout, element_justification='center', visible=False, key='streak_layout'),
           sg.Column(results_layout, element_justification='center', visible=False, key='results_layout'),  sg.Column(recommend_layout, element_justification='center', visible=False, key='recommend_layout')],
          [sg.Button('Menu', size=(20, 2)), sg.Button('Recommended Exercises', size=(20, 2))]]
# Create the window
window = sg.Window('Helping Hand', layout, element_justification='c', margins=(20,20), element_padding=(2,2), finalize=True)

# Display and interact with the Window using an Event Loop
streak_length = 0
highscore = 0
layout_mode = 'menu'
random_index = random.randint(0, len(GESTURES) - 1)
print("random index" + str(random_index))
random_gesture = GESTURES[random_index]
window['gesture_name'].update(random_gesture)
sequence = [ImageTk.PhotoImage(img) for img in ImageSequence.Iterator(Image.open('gesture_gifs/' + random_gesture + '.gif'))]
interframe_duration = Image.open('gesture_gifs/' + random_gesture + '.gif').info['duration']
# Figure
xs = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
rand = [3, 3, 3, 4, 5, 5, 6, 5, 7, 9, 8, 8, 8, 8]
fig = matplotlib.figure.Figure(figsize=(5, 4), dpi=100)
t = np.arange(0, 3, .01)
fig.add_subplot(111).plot(xs, rand)
fig.suptitle('Hand Performance History')
# fig.xlabel('Attempt Number')
# fig.ylabel('Streak Score')
# fig.set_ylim(ymin=0)
def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg

while True:
    for frame in sequence:

        event, values = window.read(timeout=interframe_duration)
        # See if user wants to quit or window was closed
        if event == sg.WINDOW_CLOSED:
            break
        if event == 'Menu':
            window['menu_layout'].update(visible=True)
            window['streak_layout'].update(visible=False)
            window['results_layout'].update(visible=False)
            window['recommend_layout'].update(visible=False)
            layout_mode = 'menu'

        if event == 'Streak Mode':
            random_index = random.randint(0, len(GESTURES) - 1)
            random_gesture = GESTURES[random_index]
            window['gesture_name'].update(random_gesture)
            sequence = [ImageTk.PhotoImage(img) for img in ImageSequence.Iterator(Image.open('gesture_gifs/' + random_gesture + '.gif'))]
            interframe_duration = Image.open('gesture_gifs/' + random_gesture + '.gif').info['duration']
            window['menu_layout'].update(visible=False)
            window['streak_layout'].update(visible=True)
            layout_mode = 'streak'
            streak_length = 0
            correct_gestures = [0]*len(GESTURES)
            window['streak_count'].update(streak_length)

        if event == 'Start Streak':
            prediction = read_gesture()
            window['-OUTPUT1-'].update('Model Prediction: ' + prediction)
            window['-OUTPUT2-'].update('Actual Gesture: ' + random_gesture)
            print('Model Prediction: ' + prediction + ' Actual Gesture: ' + random_gesture)
            print(random_gesture == prediction)
            if random_gesture == prediction:
                streak_length += 1
                print("random index" + str(random_index))
                correct_gestures[random_index] = correct_gestures[random_index] + 1
                print(correct_gestures)
                window['streak_count'].update(streak_length)
                print("streak: " + str(streak_length))
                random_index = random.randint(0, len(GESTURES) - 1)
                random_gesture = GESTURES[random_index]
                window['gesture_name'].update(random_gesture)
                sequence = [ImageTk.PhotoImage(img) for img in ImageSequence.Iterator(Image.open('gesture_gifs/' + random_gesture + '.gif'))]
                interframe_duration = Image.open('gesture_gifs/' + random_gesture + '.gif').info['duration']

            else:
                if random_gesture not in failed_gestures:
                    failed_gestures.append(random_gesture)
                    print(failed_gestures)
                if streak_length > highscore:
                    highscore = streak_length
                window['highscore'].update(highscore)
                window['streak_result'].update(streak_length)
                window['streak_layout'].update(visible=False)
                window['results_layout'].update(visible=True)
                for i in range(len(GESTURES)):
                    window[f'{GESTURES[i]}'].update(GESTURES[i] + ' '+ str(correct_gestures[i]))
                layout_mode = 'results'
        if event == 'Stats':
            fig_canvas_agg = draw_figure(window['graph1'].TKCanvas, fig)
        if event == 'History':
            fig_canvas_agg = draw_figure(window['graph2'].TKCanvas, fig)
        if event == 'Recommended Exercises':
            window['menu_layout'].update(visible=False)
            window['streak_layout'].update(visible=False)
            window['results_layout'].update(visible=False)
            window['recommend_layout'].update(visible=True)
            window['recommend'].update(failed_gestures)

        window['gif'].update(data=frame)




# Do something with the information gathered
print('Hello', values[0], "! Thanks for trying PySimpleGUI")

# Finish up by removing from the screen
window.close()
