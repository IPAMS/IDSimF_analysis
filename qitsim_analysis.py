# -*- coding: utf-8 -*-

import numpy as np
import pylab as plt
import json
import gzip
import io
import base64
from tempfile import NamedTemporaryFile
from matplotlib import animation


def read_trajectory_file(trajectoryFileName):
	"""
	Reads a trajectory file and returns a trajectory object

	Trajectory objects are dictionaries which contain three elements:
	trajectories: a vector which contains the x,y,z positions of all particles for all time steps
	(a vector of lists one vector entry per time step)
	times: vector of times of the individual time steps
	masses: the vector of particle masses

	:param trajectoryFileName: the file name of the file to read
	:return: the trajectory data dictionary
	"""
	if (trajectoryFileName[-8:] == ".json.gz"):
		with gzip.open(trajectoryFileName) as tf:
			tj = json.load(io.TextIOWrapper(tf))
	else:
		with open(trajectoryFileName) as tf:
			tj = json.load(tf)

	steps = tj["steps"]
	nIons = len(steps[0]["positions"])

	t = np.zeros([nIons,3,len(steps)])
	times = np.zeros(len(steps))
	for i in range(len(steps)):
		t[:,:,i] = np.array(steps[i]["positions"])
		times[i] = float(steps[i]["time"])

	masses = np.zeros([nIons])
	massesJson = tj["ionMasses"]
	for i in range(len(massesJson)):
		masses[i] = float(massesJson[i])
	return{"trajectories":t,"times":times,"masses":masses}


def read_QIT_conf(confFileName):
	"""
	Reads and parses the QIT simulation configuration file
	:param confFileName: the filename of the simulation configuration file
	:return: a parsed dictionary with the configuration parameters
	"""
	with open(confFileName) as jsonFile:
		confJson = json.load(jsonFile)

	return (confJson)


def filter_mass(trajectories,masses,massToFilter):
	"""
	Filters out trajectories of ions with a given mass

	:param trajectories: a trajectories vector from an imported trajectories object
	:type trajectories: trajectories vector from dict returned from readTrajectoryFile
	:param masses: a mass vector from an imported trajectories object
	:param massToFilter: the mass to filter for
	:return: a filtered trajectories vector
	"""
	massIndexes = np.nonzero(masses == massToFilter)
	return(trajectories[massIndexes,:,:][0])

def center_of_charge(tr):
	"""
	Calculates the center of charge of a charged particle cloud

	:param tr: a trajectories vector from an imported trajectories object
	:type tr: trajectories vector from dict returned from readTrajectoryFile
	:return: vector of the spatial position of the center of mass
	"""
	nSteps = np.shape(tr)[2]
	coc = np.zeros([nSteps,3])
	for i in range(nSteps):
		xMean = np.mean(tr[:,0,i])
		yMean = np.mean(tr[:,1,i])
		zMean = np.mean(tr[:,2,i])
		coc[i,:] = np.array([xMean,yMean,zMean])
	return(coc)


def load_FFT_record(projectPath):
	"""
	Loads a fft record file, which contains the mean position of the charged particle cloud over the time

	:param projectPath: path of the simulation project
	:return: two vectors: the time and the mean position of the charged particle cloud from the fft file
	"""
	dat = np.loadtxt(projectPath + "_fft.txt")
	t = dat[:, 0]
	z = dat[:, 3]
	return t,z

def reconstruct_transient_from_trajectories(dat):
	"""
	Reconstructs a QIT transient (center of charge position in detection, z, direction) from trajectory data
	:param dat: imported trajectories object
	:type dat: dict returned from readTrajectoryFile
	:return: two vectors: a time vector and the center of charge in z direction
	"""
	times = dat["times"] / 1
	nSteps = len(times)
	tr = dat["trajectories"]
	result = np.zeros([nSteps, 1])
	for i in range(nSteps):
		r = np.sqrt(tr[:, 0, i] ** 2.0 + tr[:, 1, i] ** 2.0 + tr[:, 2, i] ** 2.0)
		valid = np.nonzero(r < 5)
		result[i, 0] = np.mean(tr[valid, 2, i])
	return times,result


def get_FFT_spectrum(t,z):
	"""
	Calculates the spectrum via fft from a given transient
	:param t: the time vector of the transient
	:param z: the mean position of the charged particle cloud in detection direction
	:return: two vectors: the frequency and the intensity vectors
	"""
	n = len(t)  # length of the signal
	Fs = float(n) / (t[-1] - t[0])
	Y = np.fft.fft(z) / n  # fft computing and normalization
	Y = Y[range(n // 2)]

	k = np.arange(n)
	T = n / Fs
	frq = k / T  # two sides frequency range
	frq = frq[range(n // 2)]  # one side frequency range

	return frq,abs(Y)


def analyse_FFT_sim(projectPath,freqStart=0.0,freqStop=1.0,ampMode="lin",loadMode="fft_record"):
	"""
	Analyses a transient of a QIT simulation and calculates/plots the spectrum from it

	:param projectPath: base path of a qit simulation
	:param freqStart: start of the plotted frequency window (normalized)
	:param freqStop: stop/end of the plotted frequency window (normalized)
	:param ampMode: fft spectrum plot mode, linear or logarithmic, options: "lin" or "log"
	:param loadMode: load a recorded fft record file
	("fft_record") or reconstruct transient from trajectories ("reconstruct_from_trajectories")
	:return: a dictionary with the frequencies and amplitudes of the spectrum and
	the time vector and amplitude of the transient
	"""
	with open(projectPath + "_conf.json") as jsonFile:
		confJson = json.load(jsonFile)

	if loadMode == "fft_record":
		t,z = load_FFT_record(projectPath)
	elif loadMode == "reconstruct_from_trajectories":
		tr = read_trajectory_file(projectPath + "_trajectories.json.gz")
		t,z = reconstruct_transient_from_trajectories(tr)
		t= t*1e-6
		print(t)

	frq,Y = get_FFT_spectrum(t,z)

	fig, ax = plt.subplots(1, 2,figsize=[20,5],dpi=50)
	ax[0].plot(t,z)
	ax[0].set_xlabel('Time (s)')
	ax[0].set_ylabel('Amplitude (arb.)')

	freqsPl= range(int(len(frq)*freqStart),int((len(frq)*freqStop)))

	#ax[1].semilogy(frq[freqsPl],abs(Y[freqsPl]),'r') # plotting the spectrum
	if ampMode == "lin":
		ax[1].plot(frq[freqsPl],abs(Y[freqsPl]),'r') # plotting the spectrum
	elif ampMode == "log":
		ax[1].semilogy(frq[freqsPl], abs(Y[freqsPl]), 'r')  # plotting the spectrum logarithmic
	ax[1].set_xlabel('Freq (Hz)')
	ax[1].set_ylabel('Amplitude (arb.)')

	projectName = projectPath.split("/")[-1]
	if "space_charge_factor" in confJson:
		titlestring = projectName+" p:"+str(confJson["background_pressure"])+" Pa, c gas mass:"+str(confJson["collision_gas_mass_amu"])+" amu, "
		titlestring = titlestring + "space charge factor:"+'%6g' % (confJson["space_charge_factor"])
	else:
		titlestring = projectName+" p:"+str(confJson["background_pressure"])+" Pa"


	#titlestring = titlestring + ", nIons:"+str(confJson["n_ions"])+ ", ion masses:"+str(confJson["ion_masses"])
	plt.figtext(0.1,0.94,titlestring,fontsize=17)

	plt.savefig(projectName+"_fftAnalysis.pdf",format="pdf")
	plt.savefig(projectName+"_fftAnalysis.png",format="png")

	return({"freqs":frq[freqsPl],"amplitude":abs(Y[freqsPl]),"time":t,"transient":z})


def centerOfChargesSimulation(dat,speciesMasses,tRange=[]):
	"""
	Calculates the center of charges for two species, defined by their mass, from a simulation
	:param dat: imported trajectories object
	:type dat: dict returned from readTrajectoryFile
	:param speciesMasses: two element list with two particle masses
	:type speciesMasses: list
	:param tRange: a list / vector with time step indices to export the center of charges for
	:type tRange: list
	:return: dictionary with the time vector in "t", and the center of species a and b and of the whole
	ion cloud in dat in "cocA", "cocB" and "cocAll"
	:rtype dictionary
	"""
	masses = dat["masses"]
	times = dat["times"]

	if len(tRange)==0:
		tRange=range(len(times))
	else:
		times=times[tRange]

	tr = dat["trajectories"][:,:,tRange]

	cocA = center_of_charge(filter_mass(tr,masses,speciesMasses[0]))
	cocB = center_of_charge(filter_mass(tr,masses,speciesMasses[1]))
	cocAll = center_of_charge(tr)

	return{"t":times,"cocA":cocA,"cocB":cocB,"cocAll":cocAll}


def animate_simulation_z_vs_x(dat,masses,nFrames,interval,frameLen,zLim=3,xLim=0.1):
	"""
	Animate the center of charges of the ion clouds in a QIT simulation in a z-x projection. The center of charges
	are rendered as a trace with a given length (in terms of simulation time steps)

	:param dat: imported trajectories object
	:type dat: dict returned from readTrajectoryFile
	:param masses: two element list with two particle masses to render the center of charges for
	:type masses: list
	:param nFrames: number of frames to export
	:param interval: interval in terms of time steps in the input data between the animation frames
	:param frameLen: length of the trace of the center of charges (in terms of simulation time steps)
	:param zLim: limits of the rendered spatial section in z direction
	:param xLim: limits of the rendered spatial section in x direction
	:return: an animation object with the rendered animation
	"""
	fig = plt.figure()
	ax = plt.axes(ylim=(-zLim, zLim), xlim=(-xLim, xLim))
	lA, = ax.plot([], [], lw=2)
	lB, = ax.plot([], [], lw=2)
	lall, = ax.plot([], [], lw=2)

	# animation function.  This is called sequentially
	def animate(i):
		#x = np.linspace(0, 2, 1000)
		#y = np.sin(2 * np.pi * (x - 0.01 * i))
		tRange=np.arange(0+i*interval,frameLen+i*interval)
		d = centerOfChargesSimulation(dat,masses,tRange=tRange)
		z = d["cocA"][:,2]
		x = d["cocA"][:,0]
		lA.set_data(x,z)
		z = d["cocB"][:,2]
		x = d["cocB"][:,0]
		lB.set_data(x,z)
		z = d["cocAll"][:,2]
		x = d["cocAll"][:,0]
		lall.set_data(x,z)

		return lA,lB,lall

	# call the animator.  blit=True means only re-draw the parts that have changed.
	anim = animation.FuncAnimation(fig, animate,
								   frames=nFrames, blit=True)
	# call our new function to display the animation
	return(anim)


def plot_density_z_vs_x(trajectories,timeIndex):
	"""
	Renders an density plot in a z-x projection
	:param trajectories: a trajectories vector from an imported trajectories object
	:type trajectories: trajectories vector from dict returned from readTrajectoryFile
	:param timeIndex: index of the time step to render
	"""
	xedges = np.linspace(-10,10,80)
	zedges = np.linspace(-10,10,80)
	x = trajectories[:,0,timeIndex]
	z = trajectories[:,2,timeIndex]
	H, xedges, yedges = np.histogram2d(z,x, bins=(xedges, zedges))
	fig = plt.figure(figsize=(7, 7))


	ax = fig.add_subplot(111)
	ax.set_title('NonUniformImage: interpolated')
	im = plt.image.NonUniformImage(ax, interpolation='bilinear')
	xcenters = xedges[:-1] + 0.5 * (xedges[1:] - xedges[:-1])
	zcenters = zedges[:-1] + 0.5 * (zedges[1:] - zedges[:-1])
	im.set_data(xcenters, zcenters, H)
	ax.images.append(im)
	ax.set_xlim(xedges[0], xedges[-1])
	ax.set_ylim(zedges[0], zedges[-1])
	ax.set_aspect('equal')
	plt.show()


def animate_simulation_z_vs_x_density(dat,masses,nFrames,interval,
										fileMode='video',
										mode="lin",
										sLim=3,nBins=100,
										alphaFactor = 1,colormap = plt.cm.coolwarm,
										annotateString=""):
	"""
	Animate the center of charges of the ion clouds in a QIT simulation in a z-x projection. The center of charges
	are rendered as a trace with a given length (in terms of simulation time steps)

	:param dat: imported trajectories object
	:type dat: dict returned from readTrajectoryFile
	:param masses: two element list with two particle masses to render the center of charges for
	:type masses: list
	:param nFrames: number of frames to export
	:param interval: interval in terms of time steps in the input data between the animation frames
	:param fileMode: render either a video ("video") or single frames as image files ("singleFrame")
	:param mode: scale density linearly ("lin") or logarithmically ("log")
	:param sLim: spatial limits of the rendered spatial domain (given as distance from the origin of the coordinate system)
	:param nBins: number of density bins in the spatial directions
	:param alphaFactor: blending factor for graphical blending the densities of the two species
	:param colormap: a colormap for the density rendering (a pure species will end up on one side of the colormap)
	:param annotateString: an optional string which is rendered into the animation as annotation
	:return: animation object or figure (depends on the file mode)
	"""


	times = dat[0]["times"]
	datA = filter_mass(dat[0]["trajectories"],dat[0]["masses"],masses[0])
	datB = filter_mass(dat[1]["trajectories"],dat[1]["masses"],masses[1])

	if fileMode=='video':
		fig = plt.figure(figsize=[10,10])
	elif fileMode=='singleFrame':
		fig = plt.figure(figsize=[ 6, 6])

	xedges = np.linspace(-sLim,sLim,nBins)
	zedges = np.linspace(-sLim,sLim,nBins)
	H = np.random.rand(len(xedges),len(zedges))
	ax = plt.axes(ylim=(zedges[0], zedges[-1]), xlim=(xedges[0], xedges[-1]))

	im1 = ax.imshow(H, interpolation='nearest', origin='low', alpha=1, vmin=0, vmax=10, cmap="Reds",
				extent=[xedges[0], xedges[-1], zedges[0], zedges[-1]])

	text_time = ax.annotate("TestText",xy=(0.02,0.96),xycoords="figure fraction",
	                        horizontalalignment="left",
	                        verticalalignment="top",
	                        fontsize=20);

	plt.xlabel("r (mm)")
	plt.ylabel("z (mm)")
	fillChannel = np.ones([len(xedges)-1,len(zedges)-1])

	def animate(i):
		tsNumber = i*interval
		x = datA[:,0,tsNumber]
		z = datA[:,2,tsNumber]
		h_A, xedges2, zedges2 = np.histogram2d(z,x, bins=(xedges, zedges))
		#im1.set_array(H2);

		x = datB[:,0,tsNumber]
		z = datB[:,2,tsNumber]
		h_B, xedges2, zedges2 = np.histogram2d(z,x, bins=(xedges, zedges))

		nf_A = np.max(h_A)
		nf_B = np.max(h_B)

		rel_conc = h_A / (h_A + h_B + 0.00001)
		img_data_RGB = colormap(rel_conc)
		h_A_log = np.log10(h_A + 1)
		h_B_log = np.log10(h_B + 1)
		nf_A_log = np.max(h_A_log)
		nf_B_log = np.max(h_B_log)
		abs_dens = (h_A + h_B) / (nf_A + nf_B)
		abs_dens_log_raw = (h_A_log + h_B_log) / (nf_A_log + nf_B_log)
		abs_dens_log = abs_dens_log_raw * 0.5
		nonzero = np.nonzero(abs_dens_log > 0)
		abs_dens_log[nonzero] = abs_dens_log[nonzero] + 0.5

		if mode == "lin":
			img_data_RGB[:, :, 3] = abs_dens*alphaFactor
		elif mode== "log":
			img_data_RGB[:, :, 3] = abs_dens_log*alphaFactor

		im1.set_array(img_data_RGB)
		text_time.set_text("t="+str(times[tsNumber])+u"µs"+" "+annotateString)

		return im1

	# call the animator.  blit=True means only re-draw the parts that have changed.
	if fileMode == 'video':
		anim = animation.FuncAnimation(fig, animate, frames=nFrames, blit=False)
		return (anim)
	elif fileMode == 'singleFrame':
		animate(nFrames)
		return (fig)


#### animation / jupyter stuff ####
##animation machinery:
#http://jakevdp.github.io/blog/2013/05/12/embedding-matplotlib-animations/

VIDEO_TAG = """<video controls>
 <source src="data:video/x-m4v;base64,{0}" type="video/mp4">
 Your browser does not support the video tag.
</video>"""

def anim_to_html(anim):
	"""
	converts an animation to html (for jupyter notebooks)
	:param anim:
	:return:
	"""
	if not hasattr(anim, '_encoded_video'):
		with NamedTemporaryFile(suffix='.mp4') as f:
			anim.save(f.name, fps=20, extra_args=['-vcodec', 'libx264'])
			video = open(f.name, "rb").read()
		anim._encoded_video = base64.b64encode(video)#.encode("base64")

	return VIDEO_TAG.format(anim._encoded_video)

from IPython.display import HTML

def display_animation(anim):
	"""
	displays an animation (in an jupyter notebook)
	"""
	plt.close(anim._fig)
	return HTML(anim_to_html(anim))