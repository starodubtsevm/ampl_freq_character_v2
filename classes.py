#!/usr/bin/env python3
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
import sounddevice as sd
import sys
import queue
import numpy as np
import time

''' Class for AFC meter '''

#---------------------------------------
class afc_device(object):

	def __audio_callback (self,indata, outdata, frames, time, status):
		"""callback function"""
		if status:
			print(status, file=sys.stderr)
#--передача-потока на аудиовыход--------------------------------------------

		t = (self.start_idx + np.arange(frames)) / (sd.default.samplerate)
		t = t.reshape(-1, 1)
		outdata[:] = self.amplitude * np.sin(2 * np.pi * self.frequency * t)
		self.start_idx += frames
#--прием потока с микрофоного входа-------------------------------------
		self.q.put(indata[::self.downsample, self.mapping])


	def __init__(self, amplitude = 0.1,frequency = 150,
					blocksize = 1024, samplerate = 16000,
					freq_min = 150,freq_max=1000,freq_step=50,
					time_conv = 1):
		"""initialization"""
		self.Uref = 0.35
		self.downsample = 1
		self.start_idx = 0
		self.flag_start = 1
		self.start = 0
		self.x = []
		self.y = []
		self.frequency = freq_min
		self.channels = [2]
		self.amplitude = amplitude
		self.freq_min = freq_min
		self.freq_max = freq_max
		self.freq_step = freq_step
		self.time_conv = time_conv
		self.data_mean = 0
		self.downsample = 1
		sd.default.blocksize = blocksize
		sd.default.samplerate = samplerate
		sd.default.channels = 2
		self.q = queue.Queue()
		self.stream = sd.Stream(device = (sd.default.device, sd.default.device),
									callback = self.__audio_callback)
		self.stream.start()
		print("create")
		self.mapping = [c - 1 for c in self.channels]
		self.figure = self.plotting(samplerate)
		ani = FuncAnimation(self.figure, self.update_plot, interval = 50, blit = True)
		plt.show()

	def set_param(self, freq, ampl):
		"""set generator parametrs"""
		self.frequency = freq
		self.amplitude = ampl
		return 1

	def calc(self,data):
		"""calculation rms on current frequency"""

		if self.flag_start == 1:
			self.start = time.time()
			self.flag_start = 0 

		if time.time() - self.start >= self.time_conv:
			rms = np.sqrt(np.mean(np.square(data)))
			data = rms
			self.data_mean = np.mean(data)
			print(self.frequency,self.data_mean)
			self.x.append(self.frequency)
			self.y.append(20*np.log10(self.data_mean/self.Uref))
			self.frequency += self.freq_step
			self.flag_start = 1
			#figure.ax.set_title("Входной сигнал. СКЗ = %d у.е." % (data_mean))
			if self.frequency > self.freq_max:
				fig, ax = plt.subplots()
				ax.axis((self.freq_min, self.freq_max, -30, 3))
				ax.set_title("АЧХ устройства. Время замера = %d сек"
													 % (self.time_conv))
				ax.yaxis.grid(True)
				ax.xaxis.grid(True)
				ax.set_xlabel('частота, Hz')
				ax.set_ylabel('коэфф передачи, dB')
				plt.plot( self.x,self.y, linewidth=5, color='blue')
				self.stream.stop()
				plt.show()
				return 0
		return 1

	def update_plot(self,frame):
		"""This is called by matplotlib for each plot update.
		Typically, audio callbacks happen more frequently than plot updates,
		therefore the queue tends to contain multiple blocks of audio data.
		"""
		global plotdata
		global lines

		while True:
			try:
				data = self.q.get_nowait()
			except queue.Empty:
				break

			shift = len(data)
			if self.calc(data) == 0:
				 raise SystemExit

			plotdata = np.roll(plotdata, -shift, axis=0)
			plotdata[-shift:, :] = data

		for column, line in enumerate(lines):
			line.set_ydata(plotdata[:, column])
		return lines
	
	def plotting(self,samplerate):

		global plotdata
		global lines
		global data_mean

		length = int(250 * samplerate / (1000 * self.downsample))
		plotdata = np.zeros((length, len(self.channels)))
		fig, ax = plt.subplots()
		lines = ax.plot(plotdata)
		if len(self.channels) > 1:
			ax.legend(['channel {}'.format(c) for c in self.channels],
				loc='lower left', ncol=len(self.channels))
		ax.axis((0, len(plotdata), -1.0, 1.0))
		ax.set_xlabel('время')
		ax.set_ylabel('амплитуда, уе')
		plt.title("Входной сигнал")
		#ax.set_title("Входной сигнал. СКЗ = %d у.е." % (self.data_mean))
		ax.yaxis.grid(True)
		ax.tick_params(bottom=True, top=False, labelbottom=True,
				right=False, left=True, labelleft=True)
		return fig


