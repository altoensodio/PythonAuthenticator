# PythonAuthenticator
TOTP authenticator writen in Python

i made this bc my phone was dying lol (sorry if i write this like a caveman, english is not my main language)

![Demo](https://i.imgur.com/BDaVUt7.png)

## Installation

### Requirements
- requirements.txt
- Python 3.1X

### Pre-built binary
Install dependencies

```bash
$ pip install -r requirements.txt
```

Download the lastest binary from [here](https://github.com/altoensodio/PythonAuthenticator/releases/)

```bash
$ chmod 777 pyauth
$ mv pyauth /usr/bin/
```

### Build the binary from source
Clone the repository
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
$ PYTHONLIBVER=python$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')$(python3-config --abiflags)
gcc -Os $(python3-config --includes) main.c -o pyauth $(python3-config --ldflags) -l$PYTHONLIBVER
$ chmod 777 pyauth
$ mv pyauth /usr/bin/
```

## Usage
If you leave in blank the ID/name argument in:
- del-key
- del-keyfile
- show-code
- mod-key
- recover-key
- encrypt-keyfile

a list will be prompted to choose the ID/key/name etc...

### Add key
```bash
$ pyauth add-key name issuer key
```
### Delete key
```bash
$ pyauth del-key ID
$ pyauth del-key --issuer Issuer # search key for issuer, provider, etc.
$ pyatuh del-key --d ID # the key will not be stored in the trash file and will be deleted definitely.
```
### Show specific code
```bash
$ pyauth show-code ID
$ pyauth show-code --e key  # this gonna show a code outside the key file.
$ pyauth show-code --issuer Issuer # search codes for issuer, provider, etc.
$ pyauth show-code --e --t key # you can use --t argument to show the time left of the current code.
$ pyauth show-code ID --t
$ pyauth show-code --issuer --t Issuer
```
### Show keys from key file
```bash
$ pyauth keys
$ pyauth keys --t # show time left of current codes.
```
### Generate key
```bash
$ pyauth gen-key # generate and prints the key
$ pyauth gen-key --save name issuer # generate and saves the new key
```
### Modify key
```bash
$ pyauth mod-key ID
$ pyauth mod-key --isuser GitHub # search key for issuer, provider, etc.
```
### Clean trash
```bash
# if you delete a key without the --d option will be stored in the trash file.
$ pyauth clean-trash # delete ALL of the keys stored in the trash file.
```
### Recover deleted keys
```bash
$ pyauth recover-key file ## replace file with the name of the keyfile the key was originally
```
### Create a new key file
```bash
$ pyauth add-keyfile name
$ pyauth add-keyfile --encrypted name  # the key file will be encrypted with base64
```
### Delete a key file
```bash
$ pyauth del-keyfile name
```
### Encrypt an existing key file
```bash
$ pyauth encrypt-keyfile name
```

## Libraries used
- [pyotp](https://github.com/pyauth/pyotp)
- [typer](https://github.com/tiangolo/typer)
- [tabulate](https://github.com/astanin/python-tabulate)
- [inquirer](https://github.com/magmax/python-inquirer)
- [cryptography](https://github.com/pyca/cryptography)

## Contributing
Contributions should include tests and an explanation for the changes they propose. Documentation (examples, README.md) should be updated accordingly. Besides that feel free to contribute :)

## Contributors
altoensodio
