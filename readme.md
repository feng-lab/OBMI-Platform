## Installation
### Setup:
* install miniconda from https://docs.conda.io/en/latest/miniconda.html
* For windows, go to start menu, open `Anaconda Prompt (Miniconda3)`, conda base enviroment should be activated. For other systems, open terminal
    ```bash
    # cmd prompt should be something like (base) C:\Users\..., indicating the base conda enviroment is activated now

    # create an enviroment
    mamba create -n bmi
    # switch to bmi enviroment
    conda activate bmi  # enter bmi

    # some other conda stuff
    # to list current installed packages:
    conda list
    # to update conda
    conda update --all -y
    # to remove outdated conda packages
    conda clean --all -y
    ```
* install other enviroment for python
    ```bash
    # make sure we are in bmi enviroment (conda activate bmi)
    # this will install packages for python
    conda install pyside2 opencv pandas scipy comtypes h5py
    # to show that PySide2 is successfully installed
    conda list    # will show something like  pyside2                   5.13.1           py38ha8f7116_6    conda-forge
    ```
* install pytorch with CUDA, you can get command from https://pytorch.org/get-started/locally/

* install your ide, I am using pycharm, it's free.
* download source code
* open the obmi folder with pycharm, In `Preferences` of pycharm, set the `Project Interpreter` to our bmi enviroment (add python interpreter -> conda enviroment -> existing enviroment, our `bmi` should be there). open `src/main.py`, open context menu (right click), click 'Run main'. 
