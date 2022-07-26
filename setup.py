# coding: utf-8

from cx_Freeze import setup, Executable

executables = [Executable('main.py')]

setup(name='main_locues',
      version='1.0.1',
      description='govno_locus',
      executables=executables)