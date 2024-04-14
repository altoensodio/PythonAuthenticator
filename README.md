# PythonAuthenticator
TOTP authenticator writen in Python

i made this bc my phone was dying lol

![Demo](https://i.imgur.com/XPaO7AI.png)

## Installation

### Requirements
- requirements.txt
- Python 3.1X

### Pre-built binary
Download the lastest binary from [here](https://github.com/altoensodio/PythonAuthenticator/releases/)

```bash
$ mv pyauth /usr/bin/
```

### Build the binary from source
Clone the reposiory
```bash
$ git clone https://github.com/altoensodio/PythonAuthenticator.git
$ cd PythonAuthenticator
```
Install dependencies
```bash
$ pip install -r requirements.txt
```

Build binary

```bash
$ PYTHONLIBVER=python$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')$(python3-config --abiflags) gcc -Os $(python3-config --includes) main.c -o pyauth $(python3-config --ldflags) -l$PYTHONLIBVER
$ mv pyauth /usr/bin/
```

## Usage
### Add key
```bash
$ pyauth add-key name key
```
### Delete key
```bash
$ pyauth del-key name
```
### Show specific code
```bash
$ pyauth show-code name
$ pyauth show-code --e key  # this gonna show a code outside the key file.
```
### Show keys from key file
```bash
$ pyauth keys
```
## Examples
```bash
$ pyauth add-key example2 BASE32SECRET3232
$ pyauth del-key example2
$ pyauth show-code example
$ pyauth show-code --e BASE32SECRET3232
$ pyauth keys
```

## Libraries used
- [pyotp](https://github.com/pyauth/pyotp)
- [typer](https://github.com/tiangolo/typer)
- [tabulate](https://github.com/astanin/python-tabulate)

## Contributing
Contributions should include tests and an explanation for the changes they propose. Documentation (examples, README.md) should be updated accordingly. Besides that feel free to contribute :)

## Contributors
altoensodio
