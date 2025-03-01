
.. _install:

Installation
============

User Installation
-----------------

Create Your Local Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some dependencies require non-Python packages to work
(particularly the front-end stack that is part of the Jupyter ecosystem).
We recommend using `Miniconda <https://docs.conda.io/en/latest/miniconda.html>`_
to easily manage a compatible Python environment for ``lcviz``; it should work
with most modern shells, except CSH/TCSH.

You may want to consider installing ``lcviz`` in a new virtual or conda environment
to avoid version conflicts with other packages you may have installed, for example:

.. code-block:: bash

    conda create -n lcviz-env python=3.11
    conda activate lcviz-env

Pip Install
^^^^^^^^^^^

To install the latest stable release:

.. code-block:: bash

    pip install lcviz --upgrade

Common Issues
^^^^^^^^^^^^^

Note that ``lcviz`` requires Python 3.10 or newer. If your ``pip`` corresponds to an older version of
Python, it will raise an error that it cannot find a valid package.

Users occasionally encounter problems running the pure ``pip`` install above. For those
using ``conda``, some problems may be resolved by pulling the following from ``conda``
instead of ``pip``:

.. code-block:: bash

    conda install bottleneck
    conda install -c conda-forge notebook
    conda install -c conda-forge jupyterlab

You might also want to enable the ``ipywidgets`` notebook extension, as follows:

.. code-block:: bash

    jupyter nbextension enable --py widgetsnbextension

Developer Installation
----------------------

If you wish to contribute to ``lcviz``, please fork the project to your
own GitHub account. The following instructions assume your have forked
the project and have connected
`your GitHub to SSH <https://docs.github.com/en/authentication/connecting-to-github-with-ssh>`_
and ``username`` is your GitHub username. This is a one-setup setup:

.. code-block:: bash

    git clone git@github.com:username/lcviz.git
    cd lcviz
    git remote add upstream git@github.com:spacetelescope/lcviz.git
    git fetch upstream main
    git fetch upstream --tags

To work on a new feature or bug-fix, it is recommended that you build upon
the latest dev code in a new branch (e.g., ``my-new-feature``).
You also need the up-to-date tags for proper software versioning:

.. code-block:: bash

    git checkout -b my-new-feature
    git fetch upstream --tags
    git fetch upstream main
    git rebase upstream/main

For the rest of contributing workflow, it is very similar to
`how to make code contribution to astropy <https://docs.astropy.org/en/latest/development/workflow/development_workflow.html>`_,
except for the change log.
If your patch requires a change log, see ``CHANGES.rst`` for examples.

To install ``lcviz`` for development or from source in an editable mode
(i.e., changes to the locally checked out code would reflect in runtime
after you restarted the Python kernel):

.. code-block:: bash

    pip install -e .

Optionally, to enable the hot reloading of Vue.js templates, install
``watchdog``:

.. code-block:: bash

    pip install watchdog

After installing ``watchdog``, to use it, add the following to the top
of a notebook:

.. code-block:: python

    from lcviz import enable_hot_reloading
    enable_hot_reloading()
