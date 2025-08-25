# README

This is a modified version of Basilisk project.

- feat: removing SWIG c/c++ -> python interface and added c++ dependencies 
  Eigen & cspice library manually.

### build script

```shell
python config_and_build.py
```

this script will configure cmake and build targets to `dist3/`

```shell
python install.py
```
running after build, this script will install libraries and `.h` header 
files to directory `install/`

```shell
python run_all_test.py
```
this script will run all tests under `dist3/` directory