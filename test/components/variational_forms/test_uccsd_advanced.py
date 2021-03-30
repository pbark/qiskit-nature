# This code is part of Qiskit.
#
# (C) Copyright IBM 2019, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

""" Test of UCCSD and HartreeFock extensions """

import unittest

from test import QiskitNatureTestCase
from qiskit import BasicAer
from qiskit.utils import QuantumInstance
from qiskit.algorithms import VQE
from qiskit.algorithms.optimizers import SLSQP
from qiskit_nature import QiskitNatureError
from qiskit_nature.circuit.library import HartreeFock
from qiskit_nature.components.variational_forms import UCCSD
from qiskit_nature.mappers.second_quantization import ParityMapper
from qiskit_nature.operators.second_quantization.qubit_converter import QubitConverter
from qiskit_nature.drivers import PySCFDriver, UnitsType
from qiskit_nature.algorithms.ground_state_solvers import GroundStateEigensolver
from qiskit_nature.transformations import (FermionicTransformation,
                                           FermionicTransformationType,
                                           FermionicQubitMappingType)

# pylint: disable=invalid-name


@unittest.skip("Skip test until refactored.")
class TestUCCSDHartreeFock(QiskitNatureTestCase):
    """Test for these extensions."""

    def setUp(self):
        super().setUp()
        try:
            self.molecule = "H 0.000000 0.000000 0.735000;H 0.000000 0.000000 0.000000"
            self.driver = PySCFDriver(atom=self.molecule,
                                      unit=UnitsType.ANGSTROM,
                                      charge=0,
                                      spin=0,
                                      basis='631g')
            self.qubit_converter = QubitConverter(mapper=ParityMapper())
            self.fermionic_transformation = \
                FermionicTransformation(transformation=FermionicTransformationType.FULL,
                                        qubit_mapping=FermionicQubitMappingType.PARITY,
                                        two_qubit_reduction=True,
                                        freeze_core=True,
                                        orbital_reduction=[])
            self.qubit_op, _ = self.fermionic_transformation.transform(self.driver)

            self.reference_energy_pUCCD = -1.1434447924298028
            self.reference_energy_UCCD0 = -1.1476045878481704
            self.reference_energy_UCCD0full = -1.1515491334334347
            # reference energy of UCCSD/VQE with tapering everywhere
            self.reference_energy_UCCSD = -1.1516142309717594
            # reference energy of UCCSD/VQE when no tapering on excitations is used
            self.reference_energy_UCCSD_no_tap_exc = -1.1516142309717594
            # excitations for succ
            self.reference_singlet_double_excitations = [[0, 1, 4, 5], [0, 1, 4, 6], [0, 1, 4, 7],
                                                         [0, 2, 4, 6], [0, 2, 4, 7], [0, 3, 4, 7]]
            # groups for succ_full
            self.reference_singlet_groups = [[[0, 1, 4, 5]], [[0, 1, 4, 6], [0, 2, 4, 5]],
                                             [[0, 1, 4, 7], [0, 3, 4, 5]], [[0, 2, 4, 6]],
                                             [[0, 2, 4, 7], [0, 3, 4, 6]], [[0, 3, 4, 7]]]
        except QiskitNatureError:
            self.skipTest('PYSCF driver does not appear to be installed')

    def test_uccsd_hf_qpUCCD(self):
        """ paired uccd test """

        optimizer = SLSQP(maxiter=100)

        initial_state = HartreeFock(
            self.fermionic_transformation.molecule_info['num_orbitals'],
            self.fermionic_transformation.molecule_info['num_particles'],
            qubit_converter=self.qubit_converter)

        var_form = UCCSD(
            num_orbitals=self.fermionic_transformation.molecule_info['num_orbitals'],
            num_particles=self.fermionic_transformation.molecule_info['num_particles'],
            active_occupied=None, active_unoccupied=None,
            initial_state=initial_state,
            qubit_mapping=self.fermionic_transformation._qubit_mapping,
            two_qubit_reduction=self.fermionic_transformation._two_qubit_reduction,
            num_time_slices=1,
            shallow_circuit_concat=False,
            method_doubles='pucc',
            excitation_type='d'
        )

        solver = VQE(var_form=var_form, optimizer=optimizer,
                     quantum_instance=QuantumInstance(
                         backend=BasicAer.get_backend('statevector_simulator')))

        gsc = GroundStateEigensolver(self.fermionic_transformation, solver)

        result = gsc.solve(self.driver)

        self.assertAlmostEqual(result.total_energies[0], self.reference_energy_pUCCD, places=6)

    def test_uccsd_hf_qUCCD0(self):
        """ singlet uccd test """

        optimizer = SLSQP(maxiter=100)
        initial_state = HartreeFock(
            self.fermionic_transformation.molecule_info['num_orbitals'],
            self.fermionic_transformation.molecule_info['num_particles'],
            qubit_converter=self.qubit_converter)

        var_form = UCCSD(
            num_orbitals=self.fermionic_transformation.molecule_info['num_orbitals'],
            num_particles=self.fermionic_transformation.molecule_info['num_particles'],
            active_occupied=None, active_unoccupied=None,
            initial_state=initial_state,
            qubit_mapping=self.fermionic_transformation._qubit_mapping,
            two_qubit_reduction=self.fermionic_transformation._two_qubit_reduction,
            num_time_slices=1,
            shallow_circuit_concat=False,
            method_doubles='succ',
            excitation_type='d'
        )

        solver = VQE(var_form=var_form, optimizer=optimizer,
                     quantum_instance=QuantumInstance(
                         backend=BasicAer.get_backend('statevector_simulator')))

        gsc = GroundStateEigensolver(self.fermionic_transformation, solver)

        result = gsc.solve(self.driver)

        self.assertAlmostEqual(result.total_energies[0], self.reference_energy_UCCD0, places=6)

    def test_uccsd_hf_qUCCD0full(self):
        """ singlet full uccd test """

        optimizer = SLSQP(maxiter=100)

        initial_state = HartreeFock(
            self.fermionic_transformation.molecule_info['num_orbitals'],
            self.fermionic_transformation.molecule_info['num_particles'],
            qubit_converter=self.qubit_converter)

        var_form = UCCSD(
            num_orbitals=self.fermionic_transformation.molecule_info['num_orbitals'],
            num_particles=self.fermionic_transformation.molecule_info['num_particles'],
            active_occupied=None, active_unoccupied=None,
            initial_state=initial_state,
            qubit_mapping=self.fermionic_transformation._qubit_mapping,
            two_qubit_reduction=self.fermionic_transformation._two_qubit_reduction,
            num_time_slices=1,
            shallow_circuit_concat=False,
            method_doubles='succ_full',
            excitation_type='d'
        )

        solver = VQE(var_form=var_form, optimizer=optimizer,
                     quantum_instance=QuantumInstance(
                         backend=BasicAer.get_backend('statevector_simulator')))

        gsc = GroundStateEigensolver(self.fermionic_transformation, solver)

        result = gsc.solve(self.driver)
        self.assertAlmostEqual(result.total_energies[0], self.reference_energy_UCCD0full, places=6)

    def test_uccsd_hf_qUCCSD(self):
        """ uccsd tapering test using all double excitations """

        fermionic_transformation = FermionicTransformation(
            transformation=FermionicTransformationType.FULL,
            qubit_mapping=FermionicQubitMappingType.PARITY,
            two_qubit_reduction=True,
            freeze_core=True,
            orbital_reduction=[],
            z2symmetry_reduction='auto'
        )

        qubit_op, _ = fermionic_transformation.transform(self.driver)

        # optimizer
        optimizer = SLSQP(maxiter=100)

        # initial state
        init_state = HartreeFock(
            num_spin_orbitals=fermionic_transformation.molecule_info['num_orbitals'],
            num_particles=fermionic_transformation.molecule_info['num_particles'],
            qubit_converter=self.qubit_converter)

        var_form = UCCSD(
            num_orbitals=fermionic_transformation.molecule_info['num_orbitals'],
            num_particles=fermionic_transformation.molecule_info['num_particles'],
            active_occupied=None, active_unoccupied=None,
            initial_state=init_state,
            qubit_mapping=fermionic_transformation._qubit_mapping,
            two_qubit_reduction=fermionic_transformation._two_qubit_reduction,
            num_time_slices=1,
            z2_symmetries=fermionic_transformation.molecule_info['z2_symmetries'],
            shallow_circuit_concat=False,
            method_doubles='ucc',
            excitation_type='sd',
            skip_commute_test=True)

        solver = VQE(var_form=var_form, optimizer=optimizer,
                     quantum_instance=QuantumInstance(
                         backend=BasicAer.get_backend('statevector_simulator')))

        raw_result = solver.compute_minimum_eigenvalue(qubit_op, None)
        result = fermionic_transformation.interpret(raw_result)

        self.assertAlmostEqual(result.total_energies[0], self.reference_energy_UCCSD, places=6)

    def test_uccsd_hf_excitations(self):
        """ uccsd tapering test using all double excitations """

        # initial state
        init_state = HartreeFock(
            num_spin_orbitals=self.fermionic_transformation.molecule_info['num_orbitals'],
            num_particles=self.fermionic_transformation.molecule_info['num_particles'],
            qubit_converter=self.qubit_converter)

        # check singlet excitations
        var_form = UCCSD(
            num_orbitals=self.fermionic_transformation.molecule_info['num_orbitals'],
            num_particles=self.fermionic_transformation.molecule_info['num_particles'],
            active_occupied=None, active_unoccupied=None,
            initial_state=init_state,
            qubit_mapping=self.fermionic_transformation._qubit_mapping,
            two_qubit_reduction=self.fermionic_transformation._two_qubit_reduction,
            num_time_slices=1,
            z2_symmetries=self.fermionic_transformation.molecule_info['z2_symmetries'],
            shallow_circuit_concat=False,
            method_doubles='succ',
            excitation_type='d',
            skip_commute_test=True)

        double_excitations_singlet = var_form._double_excitations
        res = TestUCCSDHartreeFock.excitation_lists_comparator(
            double_excitations_singlet, self.reference_singlet_double_excitations)
        self.assertEqual(res, True)

        # check grouped singlet excitations
        var_form = UCCSD(
            num_orbitals=self.fermionic_transformation.molecule_info['num_orbitals'],
            num_particles=self.fermionic_transformation.molecule_info['num_particles'],
            active_occupied=None, active_unoccupied=None,
            initial_state=init_state,
            qubit_mapping=self.fermionic_transformation._qubit_mapping,
            two_qubit_reduction=self.fermionic_transformation._two_qubit_reduction,
            num_time_slices=1,
            z2_symmetries=self.fermionic_transformation.molecule_info['z2_symmetries'],
            shallow_circuit_concat=False,
            method_doubles='succ_full',
            excitation_type='d',
            skip_commute_test=True)

        double_excitations_singlet_grouped = var_form._double_excitations_grouped
        res_groups = TestUCCSDHartreeFock.group_excitation_lists_comparator(
            double_excitations_singlet_grouped, self.reference_singlet_groups)
        self.assertEqual(res_groups, True)

    @staticmethod
    def pop_el_when_matched(list1, list2):
        """
        Compares if in list1 and list2 one of excitations is the same (regardless of permutations of
        its elements). When same excitation is found, it returns the 2 lists without that excitation
        .

        Args:
            list1 (list): list of excitations (e.g. [[0, 2, 4, 6], [0, 2, 4, 7]])
            list2 (list): list of excitations

        Returns:
            list: list1 with one popped element if match was found
            list: list2 with one popped element if match was found
        """
        counter = 0
        for i, exc1 in enumerate(list1):
            for j, exc2 in enumerate(list2):
                for ind1 in exc1:
                    for ind2 in exc2:
                        if ind1 == ind2:
                            counter += 1
                if counter == len(exc1) and counter == len(exc2):
                    list1.pop(i)
                    list2.pop(j)
                    break
            break
        return list1, list2

    @staticmethod
    def excitation_lists_comparator(list1, list2):
        """
        Compares if list1 and list2 contain same excitations (regardless of permutations of
        its elements). Only works provided all indices for an excitation are different.

        Args:
            list1 (list): list of excitations (e.g. [[0, 2, 4, 6], [0, 2, 4, 7]])
            list2 (list): list of excitations

        Returns:
            bool: True or False, if list1 and list2 contain the same excitations
        """
        if len(list1) != len(list2):
            return False

        number_el = len(list1)

        for _ in range(number_el):
            list1, list2 = TestUCCSDHartreeFock.pop_el_when_matched(list1, list2)

        return bool(len(list1) or len(list2) in [0])

    @staticmethod
    def group_excitation_lists_comparator(glist1, glist2):
        """
        Compares if list1 and list2 contain same excitations (regardless of permutations of
        its elements). Only works provided all indices for an excitation are different.

        Args:
            glist1 (list): list of excitations (e.g. [[0, 2, 4, 6], [0, 2, 4, 7]])
            glist2 (list): list of excitations

        Returns:
            bool: True or False, if list1 and list2 contain the same excitations
        """
        if len(glist1) != len(glist2):
            return False

        number_groups = len(glist1)
        counter = 0
        for _, gr1 in enumerate(glist1):
            for _, gr2 in enumerate(glist2):
                res = TestUCCSDHartreeFock.excitation_lists_comparator(gr1, gr2)
                if res is True:
                    counter += 1

        return bool(counter == number_groups)


if __name__ == '__main__':
    unittest.main()
