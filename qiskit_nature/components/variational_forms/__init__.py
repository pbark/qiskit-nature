# This code is part of Qiskit.
#
# (C) Copyright IBM 2018, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

"""
Variational Forms (:mod:`qiskit_nature.components.variational_forms`)
========================================================================
These are chemistry specific Variational Forms where they inherit from
:class:`~qiskit.algorithms.variational_forms.VariationalForm`.
As they rely on chemistry specific knowledge and/or functions they live here.

.. currentmodule:: qiskit_nature.components.variational_forms

Variational Forms
=================

.. autosummary::
   :toctree: ../stubs/
   :nosignatures:

   UCCSD
   UVCC

"""
# TODO: to be removed (#66)

from .uccsd import UCCSD
from .uvcc import UVCC

__all__ = ['UCCSD', 'UVCC']
