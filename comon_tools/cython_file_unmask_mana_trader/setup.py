import os
from setuptools import setup
from Cython.Build import cythonize
import numpy

# Récupérer le chemin absolu du fichier courant
current_dir = os.path.dirname(os.path.abspath(__file__))

setup(
    ext_modules=cythonize(os.path.join(current_dir, "validate_permutation_cy.pyx"), language_level="3"),
    include_dirs=[numpy.get_include()]
)
