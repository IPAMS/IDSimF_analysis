import unittest
import os
import numpy as np
import IDSimPy.analysis as ia


class TestTrajectory(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		data_base_path = os.path.join('analysis', 'data')
		cls.legacy_hdf5_bare_fname = os.path.join(data_base_path, 'QIT_test_trajectory.hd5')
		cls.legacy_hdf5_aux_fname = os.path.join(data_base_path, 'QIT_test_trajectory_aux.hd5')

		cls.new_hdf5_variable_fname = os.path.join(data_base_path, 'qitSim_2019_07_variableTrajectoryQIT',
		                                           'qitSim_2019_07_22_001_trajectories.hd5')

		cls.new_hdf5_static_fname = os.path.join(data_base_path, 'qitSim_2019_07_variableTrajectoryQIT',
		                                         'qitSim_2019_07_22_002_trajectories.hd5')

		cls.legacy_hdf5_reactive_fn_a = os.path.join(data_base_path, 'qitSim_2019_04_scanningTrapTest',
		                                             'qitSim_2019_04_10_002_trajectories.hd5')
		cls.legacy_hdf5_reactive_fn_b = os.path.join(data_base_path, 'qitSim_2019_04_scanningTrapTest',
		                                             'qitSim_2019_04_15_001_trajectories.hd5')

		cls.test_json_fname = os.path.join(data_base_path, 'test_trajectories.json')
		cls.result_path = "test_results"

	def generate_test_trajectory(self, n_ions, n_steps):
		times = np.linspace(0, 5, n_steps)
		pos = np.zeros((n_ions, 3, n_steps))
		additional_attributes = np.zeros((n_ions, 4, n_steps))
		additional_attribute_names = ('param1', 'param2', 'param3', 'chemical id')

		x_pos = np.arange(0, n_ions) * 2.0
		for ts in range(n_steps):
			add_frame = np.zeros((n_ions, 4))
			add_frame[:ts, 3] = 1
			add_frame[:, :2] = ts
			additional_attributes[:, :, ts] = add_frame

			pos[:, 0, ts] = x_pos
			pos[:, 1, ts] = ts * 0.1

		result = ia.Trajectory(
			positions= pos,
			additional_attributes=additional_attributes,
			additional_attribute_names=additional_attribute_names,
			times=times
		)

		return result

	def test_trajectory_class_basic_instantiation_and_methods(self):
		n_timesteps = 5
		times = np.linspace(0, 2, n_timesteps)
		times_wrong = np.linspace(0, 2, n_timesteps+1)

		pos_static = np.zeros((10, 3, 5))
		tra_static = ia.Trajectory(positions=pos_static, times=times)
		self.assertEqual(tra_static.is_static_trajectory, True)
		with self.assertRaises(ValueError):
			ia.Trajectory(positions=pos_static, times=times_wrong)

		pos_variable = [np.zeros((3, 10)) for i in range(5)]
		tra_variable = ia.Trajectory(positions=pos_variable, times=times)
		self.assertEqual(tra_variable.is_static_trajectory, False)
		with self.assertRaises(ValueError):
			ia.Trajectory(positions=pos_variable, times=times_wrong)

		self.assertEqual(len(tra_static), n_timesteps)

	def test_trajectory_class_with_additional_parameters(self):
		tra = self.generate_test_trajectory(20, 15)

		self.assertEqual(tra.additional_attribute_names, ('param1', 'param2', 'param3', 'chemical id'))


	def test_hdf5_trajectory_reading_variable_timesteps(self):
		tra = ia.read_hdf5_trajectory_file(self.new_hdf5_variable_fname)

		self.assertEqual(tra['file_version_id'], 2)
		self.assertEqual(tra['static_trajectory'], False)
		self.assertEqual(np.shape(tra['positions'][9]), (512, 3))
		self.assertAlmostEqual(tra['positions'][9][500, 2], -0.000135881)

	def test_hdf5_trajectory_reading_static_timesteps(self):
		tra = ia.read_hdf5_trajectory_file(self.new_hdf5_static_fname)

		self.assertEqual(tra['file_version_id'], 2)
		self.assertEqual(tra['static_trajectory'], True)
		self.assertEqual(tra['n_particles'], 1000)
		self.assertEqual(np.shape(tra['positions']), (1000, 3, 51))
		self.assertEqual(np.shape(tra['additional_attributes']), (1000, 9, 51))
		self.assertAlmostEqual(tra['positions'][983, 0, 9], -0.00146076)

	def test_legacy_hdf5_trajectory_reading(self):
		tra = ia.read_legacy_hdf5_trajectory_file(self.legacy_hdf5_aux_fname)
		self.assertEqual(tra['n_particles'], 600)
		self.assertEqual(np.shape(tra['positions']), (600, 3, 41))
		self.assertEqual(np.shape(tra['additional_attributes']), (600, 9, 41))

	def test_basic_json_trajectory_reading(self):
		tra = ia.read_json_trajectory_file(self.test_json_fname)
		print(np.shape(tra['positions']))
		print(np.shape(tra['additional_attributes']))
		print(np.shape(tra['masses']))

	def test_parameter_filter_with_synthetic_trajectory(self):
		tra = self.generate_test_trajectory(20, 15)
		id_column = tra.additional_attribute_names.index('chemical id')
		tra_filtered_vec = ia.filter_parameter(tra.positions, tra.additional_attributes[:, id_column, 5], 1)
		self.assertTrue(isinstance(tra_filtered_vec, np.ndarray))
		self.assertEqual(np.shape(tra_filtered_vec), (5, 3, 15))

		chem_id = tra.additional_attributes[:, id_column, :]
		tra_filtered = ia.filter_parameter(tra.positions, chem_id, 1)
		self.assertTrue(isinstance(tra_filtered, list))

		n_ts = 15
		self.assertEqual(len(tra_filtered), n_ts)

		self.assertTrue(isinstance(tra_filtered[0], np.ndarray))
		self.assertTrue(isinstance(tra_filtered[1], np.ndarray))

		ts_result = np.array([[0.0, 0.3, 0.0], [2.0, 0.3, 0.0], [4.0, 0.3, 0.0]])
		np.testing.assert_allclose(tra_filtered[3], ts_result)
		for i in range(n_ts):
			self.assertEqual(np.shape(tra_filtered[i]), (i, 3))

	def test_parameter_filter_with_qit_trajectory(self):
		tra = ia.read_legacy_hdf5_trajectory_file(self.legacy_hdf5_reactive_fn_b)

		id_column = tra['additional_names'].index('chemical id')
		chem_id = tra['additional_attributes'][:, id_column, :]
		tra_filtered = [ia.filter_parameter(tra['positions'], chem_id, i) for i in (0, 1, 2)]
		for tra_f in tra_filtered:
			self.assertTrue(isinstance(tra_f, list))
			self.assertEqual(len(tra_f), 51)
