import pyotp
import json
from os.path import expanduser
from os.path import join
from os.path import exists
from os import makedirs
import typer
from tabulate import tabulate

app = typer.Typer()

PATH = join(expanduser('~'), ".config", "pyauthenticator")
JSON_PATH = join(PATH, "keys.json")

def exists_in_json(a):
    with open(JSON_PATH) as f:
        data = json.load(f)
    if a in str(data):
        return True
    else:
        return False


def verify_json():
    if exists(JSON_PATH):
        pass
    else:
        try:
            if exists("~/.config/pyauthenticator/"):
                file = open(JSON_PATH, "w")
                file.write('{"example": {"key": "base32secret3232"}}')
                file.close()
            else:
                makedirs(PATH)
                file = open(JSON_PATH, "w")
                file.write('{"example": {"key": "base32secret3232"}}')
                file.close()
        except Exception as e:
            print("Unexpected error: {}".format(e))


@app.command()
def show_code(
    name: str,
    e: bool = typer.Option(False, help="Show TOTP code of a key outside key file."),
):
    verify_json()
    if e:
        try:
            totp = pyotp.TOTP('{}'.format(name))
            print("Code: {}".format(totp.now()))
        except Exception as e:
            print("Error: {}".format(e))
    else:
        try:
            if exists_in_json(name) == True: 
                data = json.load(open(JSON_PATH))
                totp = pyotp.TOTP(data[name]["key"])
                print('"{}" code: {}'.format(name, totp.now()))
            else:
                print('"{}" not in key file.')
        except Exception as e:
            print("Error: {}".format(e))

@app.command()
def add_key(name: str, key: str):
    try:
        verify_json()
        if exists_in_json(name) == False:
            y = {"{}".format(name):{"key": "{}".format(key)}}
            with open(JSON_PATH) as f:
                data = json.load(f)
            data.update(y)
            with open(JSON_PATH, 'w') as f:
                json.dump(data, f)
            print('"{}" added to key file.'.format(name))
        else:
            print('"{}" already in key file.'.format(name))
    except Exception as e:
        print("Unexpected error: {}".format(e))


@app.command()
def del_key(name: str):
    try:
        verify_json()
        if exists_in_json(name) == True:
            data = json.load(open(JSON_PATH))
            data.pop(name)
            with open(JSON_PATH, "w") as f:
                json.dump(data, f)
            print('"{}" removed from key file.'.format(name))
        else:
            print('"{}" is not in key file.'.format(name))

    except Exception as e:
          print("Unexpected error: {}".format(e))


@app.command()
def keys():
    verify_json()
    data = json.load(open(JSON_PATH))
    key_list = [["Name", "Code"]]
    for i in data:
        key_list.append([i, pyotp.TOTP(data[i]["key"]).now()])
    
    table = tabulate(key_list,headers='firstrow', tablefmt="fancy_grid")
    print(table)


if __name__ == "__main__":
    app()
