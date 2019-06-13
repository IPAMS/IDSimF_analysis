import unittest
import os
import numpy as np
import IDSimF_analysis.trajectory as tra
import IDSimF_analysis.visualization as vis


class TestVisualization_animations(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.test_json_trajectory = os.path.join('data', 'test_trajectories.json')
		cls.test_json_projectName = os.path.join('data', 'test')
		cls.test_reactive_projectName = os.path.join('data', 'qitSim_2019_04_scanningTrapTest',
		                                          'qitSim_2019_04_15_001')
		cls.test_hdf5_trajectory_a = os.path.join('data', 'qitSim_2019_04_scanningTrapTest',
		                                          'qitSim_2019_04_10_001_trajectories.hd5')
		cls.test_hdf5_trajectory_b = os.path.join('data', 'qitSim_2019_04_scanningTrapTest',
		                                          'qitSim_2019_04_10_002_trajectories.hd5')
		cls.test_hdf5_trajectory_c = os.path.join('data', 'qitSim_2019_04_scanningTrapTest',
		                                          'qitSim_2019_04_15_001_trajectories.hd5')
		cls.result_path = "test_results"


	def test_scatter_animation_json_trajectory(self):
		resultName = os.path.join(self.result_path, 'scatter_animation_test_1')
		vis.render_scatter_animation(self.test_json_projectName, resultName,file_type='json')

	def test_scatter_animation_hdf5_trajectory(self):
		resultName = os.path.join(self.result_path, 'scatter_animation_test_2')
		vis.render_scatter_animation(self.test_reactive_projectName, resultName,alpha=0.5,color_parameter=2)


	def test_basic_scatter_animation_low_level(self):
		tra_b = tra.read_hdf5_trajectory_file(self.test_hdf5_trajectory_b)
		anim = vis.animate_scatter_plot(tra_b)
		result_name = os.path.join(self.result_path, 'scatter_animation_test_3.mp4')
		anim.save(result_name, fps=20, extra_args=['-vcodec', 'libx264'])

	def test_complex_scatter_animation_low_level(self):
		tra_b = tra.read_hdf5_trajectory_file(self.test_hdf5_trajectory_b)

		anim = vis.animate_scatter_plot(tra_b, xlim=(-0.001, 0.001), ylim=(-0.0015, 0.0015), zlim=(-0.005, 0.005),
		                                color_parameter=1,alpha = 0.4)

		result_name = os.path.join(self.result_path, 'scatter_animation_test_4.mp4')

		anim.save(result_name, fps=20, extra_args=['-vcodec', 'libx264'])

	def test_density_animation_low_level(self):
		traj_hdf5 = tra.read_hdf5_trajectory_file(self.test_hdf5_trajectory_a)
		anim = vis.animate_xz_density(traj_hdf5['positions'],
		                              xedges=np.linspace(-0.001, 0.001, 50),
		                              zedges=np.linspace(-0.001, 0.001, 50),
		                              figsize=(10, 5))

		result_name = os.path.join(self.result_path, 'density_animation_test_1.mp4')
		anim.save(result_name, fps=20, extra_args=['-vcodec', 'libx264'])

	def test_density_animation(self):
		resultName = os.path.join(self.result_path, 'density_animation_test_2')
		vis.render_xz_density_animation(self.test_reactive_projectName, resultName)


		resultName = os.path.join(self.result_path, 'density_animation_test_3')
		vis.render_xz_density_animation(self.test_reactive_projectName, resultName, xedges=10,
		                                zedges=np.linspace(-0.004, 0.004, 100),axis_equal=False)


	def test_comparison_density_animation_with_json(self):
		projectNames = [self.test_json_projectName, self.test_json_projectName]
		masses = [73,55]
		resultName = os.path.join(self.result_path, 'animation_test_1')
		vis.render_xz_density_comparison_animation(projectNames, masses, resultName, n_frames=100, interval=1, s_lim=7,
		                                           select_mode='mass',
		                                           annotation="", mode="lin", file_type='json')

	def test_comparison_animation_with_custom_limits_with_json(self):
		projectNames = [self.test_json_projectName, self.test_json_projectName]
		masses = [73,55]
		resultName = os.path.join(self.result_path, 'animation_test_2')
		vis.render_xz_density_comparison_animation(projectNames, masses, resultName, n_frames=100, interval=1,
		                                           select_mode='mass',
		                                           s_lim=[-1, 5, -1, 1],
		                                           n_bins=[100, 20],
		                                           annotation="", mode="log", file_type='json')

	def test_low_level_reactive_density_comparison_animation_with_hdf5(self):
		tra_b = tra.read_hdf5_trajectory_file(self.test_hdf5_trajectory_b)
		tra_c = tra.read_hdf5_trajectory_file(self.test_hdf5_trajectory_c)

		self.assertRaises( #too many frames: n_frames*interval > trajectory length
			ValueError,
			vis.animate_xz_density_comparison_plot, [tra_c, tra_c], [0, 1], 71, 1)

		anim = vis.animate_xz_density_comparison_plot([tra_c, tra_c], [0, 1], 51, 1, s_lim=0.001, select_mode='substance')
		result_name = os.path.join(self.result_path, 'reactive_density_animation_test_1.mp4')
		anim.save(result_name, fps=20, extra_args=['-vcodec', 'libx264'])

		self.assertRaises( #time vector length differs
			ValueError,
			vis.animate_xz_density_comparison_plot, [tra_b, tra_c], [0, 0], 71, 1)


	def test_reactive_density_comparison_animation(self):
		projectNames = [self.test_reactive_projectName, self.test_reactive_projectName]
		substances = [0,1]
		resultName = os.path.join(self.result_path, 'reactive_density_animation_test_2')
		vis.render_xz_density_comparison_animation(projectNames, substances, resultName, n_frames=51, interval=1,
		                                           select_mode='substance',
		                                           s_lim=0.001, annotation="", file_type='hdf5')