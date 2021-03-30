# This code is part of Qiskit.
#
# (C) Copyright IBM 2020, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""Tests of BOPES Sampler."""

import unittest
from functools import partial

import numpy as np
from qiskit import BasicAer
from qiskit.circuit.library import RealAmplitudes
from qiskit.utils import QuantumInstance, algorithm_globals
from qiskit.algorithms import VQE, NumPyMinimumEigensolver
from qiskit.algorithms.optimizers import AQGD
from qiskit.opflow import PauliExpectation
from qiskit_nature.algorithms.pes_samplers.bopes_sampler import BOPESSampler
from qiskit_nature.circuit.library import HartreeFock
from qiskit_nature.mappers.second_quantization import ParityMapper
from qiskit_nature.operators.second_quantization.qubit_converter import QubitConverter
from qiskit_nature.drivers import Molecule, PySCFDriver
from qiskit_nature.algorithms.ground_state_solvers import GroundStateEigensolver
from qiskit_nature.algorithms.pes_samplers.potentials.morse_potential import MorsePotential
from qiskit_nature.transformations import FermionicTransformation


@unittest.skip("Skip test until refactored.")
class TestBOPES(unittest.TestCase):
    """Tests of BOPES Sampler."""

    def test_h2_bopes_sampler(self):
        """Test BOPES Sampler on H2"""
        seed = 50
        algorithm_globals.random_seed = seed

        # Molecule
        dof = partial(Molecule.absolute_distance, atom_pair=(1, 0))
        m = Molecule(geometry=[['H', [0., 0., 1.]],
                               ['H', [0., 0.45, 1.]]],
                     degrees_of_freedom=[dof])

        mapper = ParityMapper()
        converter = QubitConverter(mapper=mapper)

        f_t = FermionicTransformation()
        driver = PySCFDriver(molecule=m)

        qubitop, _ = f_t.transform(driver)

        # Quantum Instance:
        shots = 1
        backend = 'statevector_simulator'
        quantum_instance = QuantumInstance(BasicAer.get_backend(backend), shots=shots)
        quantum_instance.run_config.seed_simulator = seed
        quantum_instance.compile_config['seed_transpiler'] = seed

        # Variational form
        i_state = HartreeFock(num_spin_orbitals=f_t._molecule_info['num_orbitals'],
                              num_particles=f_t._molecule_info['num_particles'],
                              qubit_converter=converter)
        var_form = RealAmplitudes(qubitop.num_qubits, reps=1, entanglement='full',
                                  skip_unentangled_qubits=False)
        var_form.compose(i_state, front=True)

        # Classical optimizer:
        # Analytic Quantum Gradient Descent (AQGD) (with Epochs)
        aqgd_max_iter = [10] + [1] * 100
        aqgd_eta = [1e0] + [1.0 / k for k in range(1, 101)]
        aqgd_momentum = [0.5] + [0.5] * 100
        optimizer = AQGD(maxiter=aqgd_max_iter,
                         eta=aqgd_eta,
                         momentum=aqgd_momentum,
                         tol=1e-6,
                         averaging=4)

        # Min Eigensolver: VQE
        solver = VQE(var_form=var_form,
                     optimizer=optimizer,
                     quantum_instance=quantum_instance,
                     expectation=PauliExpectation())

        me_gss = GroundStateEigensolver(f_t, solver)

        # BOPES sampler
        sampler = BOPESSampler(gss=me_gss)

        # absolute internuclear distance in Angstrom
        points = [0.7, 1.0, 1.3]
        results = sampler.sample(driver, points)

        points_run = results.points
        energies = results.energies

        np.testing.assert_array_almost_equal(points_run, [0.7, 1.0, 1.3])
        np.testing.assert_array_almost_equal(energies,
                                             [-1.13618945, -1.10115033, -1.03518627], decimal=2)

    def test_potential_interface(self):
        """Tests potential interface."""
        seed = 50
        algorithm_globals.random_seed = seed

        stretch = partial(Molecule.absolute_distance, atom_pair=(1, 0))
        # H-H molecule near equilibrium geometry
        m = Molecule(geometry=[['H', [0., 0., 0.]],
                               ['H', [1., 0., 0.]],
                               ],
                     degrees_of_freedom=[stretch],
                     masses=[1.6735328E-27, 1.6735328E-27])

        f_t = FermionicTransformation()
        driver = PySCFDriver(molecule=m)

        f_t.transform(driver)

        solver = NumPyMinimumEigensolver()

        me_gss = GroundStateEigensolver(f_t, solver)
        # Run BOPESSampler with exact eigensolution
        points = np.arange(0.45, 5.3, 0.3)
        sampler = BOPESSampler(gss=me_gss)

        res = sampler.sample(driver, points)

        # Testing Potential interface
        pot = MorsePotential(m)
        pot.fit(res.points, res.energies)

        np.testing.assert_array_almost_equal([pot.alpha, pot.r_0], [2.235, 0.720], decimal=3)
        np.testing.assert_array_almost_equal([pot.d_e, pot.m_shift], [0.2107, -1.1419], decimal=3)


if __name__ == "__main__":
    unittest.main()
