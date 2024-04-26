#cython: annotation_typing = False
#cython: language_level=3
import pyotp
import json
from os.path import expanduser
from os.path import join
from os.path import exists
from os import linesep
from os import makedirs
import typer
from tabulate import tabulate
import inquirer
import datetime
from time import sleep
import readchar

app = typer.Typer()

PATH = join(expanduser('~'), ".config", "pyauthenticator")
JSON_PATH = join(PATH, "keys.json")


def exists_in_json(name, issuer_name=None, complete=False):
    try:
        if complete == False:
            with open(JSON_PATH) as f:
                data = json.load(f)
            if name in data:
                return True
            else:
                return False
        else:
            data = json.load(open(JSON_PATH))
            matches = 0
            for i in data:
                if [data[i]["name"], data[i]["issuer_name"]] == [name, issuer_name]:
                    matches += 1
            if matches > 0:
                return True
            else:
                return False
    except Exception as e:
        print("Unexpected error: {}".format(e))


def data_control(x=None, delete=False):
    try:
        if delete == False:
            with open(JSON_PATH) as f:
                data = json.load(f)
            data.update(x)
            with open(JSON_PATH, "w") as f:
                json.dump(data, f)
        elif delete == True:
            data = json.load(open(JSON_PATH))
            data.pop(x)
            with open(JSON_PATH, "w") as f:
                json.dump(data, f)
    except Exception as e:
       print("Unexpected error: {}".format(e))


def verify_json():
    try:
        if exists(JSON_PATH) == True:
            data = json.load(open(JSON_PATH))
            a = [int(i) for i in data]
            res = [ele for ele in range(max(a)+1) if ele not in a]
            if res != []:
                n = 1
                new_data = {}
                for i in data:
                    new_data.update({"{}".format(n): data[i]}) 
                    n += 1
                with open(JSON_PATH, 'w') as f:
                    json.dump(new_data, f)
        else:
            if exists(PATH):
                file = open(JSON_PATH, "w")
                file.write('{"1": {"name":"example@example.com", "issuer_name":"example", "key": "base32secret3232"}}')
                file.close()
            else:
                makedirs(PATH)
                file = open(JSON_PATH, "w")
                file.write('{"1": {"name":"example@example.com", "issuer_name":"example", "key": "base32secret3232"}}')
                file.close()
    except Exception as e:
        print("Unexpected error: {}".format(e))


def get_table(header, time=False):
    data = json.load(open(JSON_PATH))
    key_list = []
    for i in data:
        totp = pyotp.TOTP("{}".format(data[i]["key"]))
        if time:
            time_remaining = int(totp.interval - datetime.datetime.now().timestamp() % totp.interval)
            key_list.append([i, data[i]["name"], data[i]["issuer_name"], totp.now(), time_remaining])
        else:
            key_list.append([i, data[i]["name"], data[i]["issuer_name"], totp.now()])
    table = tabulate(key_list,headers=header, tablefmt="fancy_grid")
    return table


def refresh_string(string):
    magic_char = '\033[F'
    del_lines = magic_char * string.count("\n")
    return del_lines


def time_left(totp):
    print(end="\n\n")
    while True:
        time_remaining = int(totp.interval - datetime.datetime.now().timestamp() % totp.interval)
        multi_line = 'Code: {}\nTime left: {} \n'.format(totp.now(), time_remaining)
        print('{}{}'.format(refresh_string(multi_line), multi_line), end='')
        sleep(1)


@app.command()
def show_code(
        key_id: str = typer.Argument(None, help="Key-ID to show code. (Use [command: keys] to see the IDs)"), 
        issuer: str = typer.Option(None, help="Search TOTP code by issuer."),
        e: bool = typer.Option(False, help="Show TOTP code of a key outside key file."),
        t: bool = typer.Option(False, help="Show the remaining time for the code to change.")
):
    verify_json()
    if e:
        try:
            totp = pyotp.TOTP('{}'.format(key_id))
            if t:
                time_left(totp)
            else:
                print("Code: {}".format(totp.now()))
        except Exception as e:
            print("Unexpected error: {}".format(e))
    elif issuer:
        try:
            data = json.load(open(JSON_PATH))
            matches = []
            for i in data:
                if data[i]["issuer_name"] == issuer:
                    matches.append(i)
            if len(matches) > 1:
                inquirer_list = [data[i]["name"] for i in matches]
                inquirer_list.append("Exit")
                q = inquirer.List("name",message="Choice one of the options to show the code.", choices=inquirer_list, default="Exit"),
                answer = inquirer.prompt(q)
                if answer["name"] != "Exit":
                    for i in matches:
                        if data[i]["name"] == answer["name"]:
                            answer = data[i]
                    totp = pyotp.TOTP("{}".format(answer["key"]))
                    if t:
                        time_left(totp)
                    else:
                        print("{}({}) code: {}".format(answer["name"], answer["issuer_name"], totp.now()))
            elif len(matches) == 1:
                totp = pyotp.TOTP("{}".format(data[matches[0]]["key"]))
                if t:
                    time_left(totp)
                else:
                    print("{}({}) code: {}".format(data[matches[0]]["name"], data[matches[0]]["issuer_name"], totp.now()))
            else:
                print('Issuer "{}" not in key file.'.format(issuer))
        except Exception as e:
            print("Unexpected error: {}".format(e))
    else:
        try:
            try:
                int(key_id)
            except ValueError:
                print("Key-ID must be a int.")
            except Exception as e:
                print("Unexpected error: {}".format(e))
            else:
                if exists_in_json(key_id) == True: 
                    data = json.load(open(JSON_PATH))
                    totp = pyotp.TOTP(data[key_id]["key"])
                    if t:
                        time_left(totp)
                    else:
                        print('{}({}) code: {}'.format(data[key_id]["name"], data[key_id]["issuer_name"], totp.now()))
                else:
                    print('ID "{}" not in key file.'.format(key_id))
        except ValueError:
            print("Key-ID must be a int.")
        except Exception as e:
            print("Unexpected error: {}".format(e))


@app.command()
def add_key(
        name: str = typer.Argument(help="Name, E-Mail, etc. Example = example@example.com"),
        issuer_name: str = typer.Argument(help="Issuer, provider, etc. Example = GitHub"),
        key: str = typer.Argument(help="Base32 key. Example = BASE32SECRET3232")
):
    try:
        verify_json()
        with open(JSON_PATH) as f:
            data = json.load(f)
        if exists_in_json(name, issuer_name, True) == True:
            print("{}({}) already in key file.".format(name, issuer_name))
        else:
            data = json.load(open(JSON_PATH))
            id_num = [i for i in data]
            new_data = {"{}".format(len(id_num) + 1): {"name": "{}".format(name), "issuer_name": "{}".format(issuer_name), "key": "{}".format(key)}}
            data_control(new_data)
            print('{}({}) added to key file.'.format(name, issuer_name))

    except Exception as e:
        print("Unexpected error: {}".format(e))


@app.command()
def del_key(
        key_id: str = typer.Argument(None, help="Key-ID to delete. Use [command: keys] to see IDs"), 
        issuer: str = typer.Option(None, help="Issuer, provider, etc. Example = GitHub")
):
    try:
        verify_json()
        if issuer:
            data = json.load(open(JSON_PATH))
            matches = []
            for i in data:
                if data[i]["issuer_name"] == issuer:
                    matches.append(i)
            if len(matches) > 1:
                inquirer_list = [data[i]["name"] for i in matches]
                inquirer_list.append("Exit")
                q = inquirer.List("name",message="Choice one of the options to delete.", choices=inquirer_list, default="Exit"),
                answer = inquirer.prompt(q)
                if answer["name"] != "Exit":
                    for i in matches:
                        if data[i]["name"] == answer["name"]:
                            answer = data[i]
                            id_num = i
                    data_control(id_num, True)
                    print("{}({}) removed from key file.".format(answer["name"], answer["issuer_name"]))
            else:
                print('Issuer "{}" not in key file.'.format(issuer))
        else:
            data = json.load(open(JSON_PATH))
            int(key_id)
            if exists_in_json(key_id) == True:
                data_control(key_id, True)
                print("{}({}) removed from key file.".format(data[key_id]["name"], data[key_id]["issuer_name"]))
            else:
                print('ID "{}" not in key file.'.format(key_id))
    except ValueError:        
        print("Key-ID must be a int.")
    except TypeError:
        print("Key-ID must be a int.")
    except Exception as e:
        print("Unexpected error: {}".format(e))


@app.command()
def keys(t: bool = typer.Option(False, help="Show the remaining time for the codes to change.")):
    try:
        verify_json()
        if t:
            table = "{}\n".format(get_table([""]))
            print("\n" * table.count("\n"), end="")
            while True:
                table = "{}\n".format(get_table(["ID", "Name", "Issuer", "Code", "Time Remaining"], True))
                print('{}{}'.format(refresh_string(table), table), end='')
                sleep(1)
        else:
            table = get_table(["ID", "Name", "Issuer", "Code"])
            print(table)
    except Exception as e:
        print("Unexpected error: {}".format(e))


@app.command()
def gen_key(
        name: str = typer.Argument(None, help="Name, E-Mail, etc. Example = example@example.com"),
        issuer_name: str = typer.Argument(None, help="Issuer, provider, etc. Example = GitHub"),
        save: bool = typer.Option(False, help="Save the generated key in the key file."),
):
    try:
        if save == True and name != None and issuer_name != None:
            key = pyotp.random_base32()
            add_key(name, issuer_name, key)
        elif save == False:
            key = pyotp.random_base32()
            print("New key: {}".format(key))
        else:
            print("Please insert valid credentials.")
    except Exception as e:
        raise Exception(e)


if __name__ == "__main__":
    app()
