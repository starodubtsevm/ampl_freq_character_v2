from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import numpy as np
import queue
from config import *
import sys
import time

q = queue.Queue()
mapping = [c - 1 for c in channels]
flag_start = 1
start = 0
x=[]
y=[]
frequency = frequency_min
data_mean = 0

def plotting(samplerate):

	global plotdata
	global lines
	global data_mean

	length = int(250 * samplerate / (1000 * downsample))
	plotdata = np.zeros((length, len(channels)))
	fig, ax = plt.subplots()
	lines = ax.plot(plotdata)
	
	if len(channels) > 1:
		ax.legend(['channel {}'.format(c) for c in channels],
			loc='lower left', ncol=len(channels))
			
	ax.axis((0, len(plotdata), -1.0, 1.0))
	ax.set_xlabel('время')
	ax.set_ylabel('амплитуда, уе')
	#ax.set_title("Входной сигнал. СКЗ = %d у.е." % (data_mean))
	
	ax.yaxis.grid(True)
	ax.tick_params(bottom=True, top=False, labelbottom=True,
				right=False, left=True, labelleft=True)

	return fig

def update_plot(frame):
	"""This is called by matplotlib for each plot update.
	Typically, audio callbacks happen more frequently than plot updates,
	therefore the queue tends to contain multiple blocks of audio data.
	"""
	global plotdata
	global lines

	while True:
		try:
			data = q.get_nowait()
		except queue.Empty:
			break

		shift = len(data)
		if calc(data) == 0: raise SystemExit

		plotdata = np.roll(plotdata, -shift, axis=0)
		plotdata[-shift:, :] = data

	for column, line in enumerate(lines):
		line.set_ydata(plotdata[:, column])
	return lines

def audio_callback(indata, outdata, frames, time, status):
	if status:

		print(status, file=sys.stderr)
#--передача-потока на аудиовыход--------------------------------------------
	global start_idx
	t = (start_idx + np.arange(frames)) / samplerate
	t = t.reshape(-1, 1)
	outdata[:] = amplitude * np.sin(2 * np.pi * frequency * t)
	start_idx += frames

#--прием потока с микрофоного входа-------------------------------------
	q.put(indata[::downsample, mapping])

def calc(data):
	"""This is ..."""

	global flag_start
	global start
	global amplitude
	global frequency
	global x,y

	if flag_start == 1:
		start = time.time()
		flag_start = 0 

	if time.time() - start >= time_conv:
		rms = np.sqrt(np.mean(np.square(data)))
		data = rms
		data_mean = np.mean(data)

		print(frequency,data_mean)
		x.append(frequency)
		y.append(20*np.log10(data_mean/Uref))
		frequency += frequency_step
		flag_start = 1
		#figure.ax.set_title("Входной сигнал. СКЗ = %d у.е." % (data_mean))
		if frequency > frequency_max:
			fig, ax = plt.subplots()
			ax.axis((frequency_min, frequency_max, -30, 3))
			ax.set_title("АЧХ устройства. Время замера = %d сек" % (time_conv))
			ax.yaxis.grid(True)
			ax.xaxis.grid(True)
			ax.set_xlabel('частота, Hz')
			ax.set_ylabel('коэфф передачи, dB')
			#plt.plot(x,y,'ko-')
			plt.plot( x,y, linewidth=5, color='blue')
			plt.show()
			return 0
	return 1

