#cython: annotation_typing = False
#cython: language_level=3
import pyotp, json, base64, hashlib, datetime, inquirer, typer
from os.path import expanduser, join, exists, isfile, splitext, basename
from os import makedirs, listdir, remove
from tabulate import tabulate
from time import sleep
from cryptography.fernet import Fernet, InvalidToken
from atexit import register
from getpass import getpass

app = typer.Typer()

PATH = join(expanduser('~'), ".config", "pyauthenticator")
TRASH_PATH = join(PATH, "trash.json")
KEYFILES_PATH = join(PATH, "keyfiles")
KEY_PATH = join(KEYFILES_PATH, "keys.json")


# Functions

def encrypt(filename: str, key, output: str):
    try:
        f = Fernet(key)
        with open(filename, "rb") as file: file_data = file.read()
        encrypted_data = f.encrypt(file_data)
        with open(output, "wb") as file: file.write(encrypted_data)
    except ValueError as e: raise ValueError(e)
    except Exception as e: raise Exception(e)
    
    
def decrypt(filename: str, key):
    try:
        f = Fernet(key)
        with open(filename, "rb") as file: encrypted_data = file.read()
        decrypted_data = f.decrypt(encrypted_data)
        return decrypted_data
    except InvalidToken:
        print("Wrong password, try again.")
        return False
    except ValueError as e: raise ValueError(e)
    except Exception as e: raise Exception(e)


def gen_passwd():
    return Fernet.generate_key()


def ask_passwd(random: bool = False):
    randompass = False
    passwd = str(getpass("\nEnter password/key: ")).encode()
    if passwd == "G".encode() and random:
        passwd = gen_passwd()
        print(f'Your password is "{passwd.decode()}" \n(WARNING: If you loose this password you will loose all the data stored in the keyfile)')
        randompass = True
    key = hashlib.md5(passwd).hexdigest()
    return base64.urlsafe_b64encode(key.encode("utf-8")) if not randompass else [base64.urlsafe_b64encode(key.encode("utf-8"))]


def sort_ids(data = None, save: bool = True):
    try:
        if not data: data = json.load(open(KEY_PATH))
        a = [int(i) for i in data]
        res = [ele for ele in range(max(a)+1) if ele not in a]
        if res != []:
            n = 1
            new_data = {}
            for i in data:
                new_data.update({f"{n}": data[i]}) 
                n += 1
            if save:
                with open(KEY_PATH, 'w') as f:
                    json.dump(new_data, f)
                    return
        return new_data
    except Exception: pass


def confirm(command, c, exit, message: str, equal: bool = False, extra = False):
    if not extra: condition = command()
    else: 
        rc = command(extra())
        condition = rc[0]
    tries = 3
    if equal:
        while condition == c:
            if condition == exit or tries == 1: return False
            tries -=1
            print(message)
            if not extra: condition = command()
            else: 
                rc = command(extra())
                condition = rc[0]
    else:
        while condition != c:
            if condition == exit or tries == 1: return False
            tries -=1
            print(message)
            if not extra: condition = command()
            else: 
                rc = command(extra())
                condition = rc[0]
    return condition if not extra else rc


def exit_handler():
    if KEY_PATH.endswith(".tmp"): remove(KEY_PATH)


def exists_in_json(name, issuer_name=None, complete=False):
    try:
        data = json.load(open(KEY_PATH))
        if not complete:
            if name in data: return True
        else:   
            matches = [i for i in data if [data[i]["name"], data[i]["issuer_name"]] == [name, issuer_name]]
            if matches != []: return True
        return False
    except Exception as e: raise Exception(e)


def encrypt_manager(mode: str = "r", keyfile: str = None):
    if mode == "r":
        print("\nThis file is encrypted.\nType the password to read the encrypted file.")
        decrypted = confirm(lambda :decrypt(join(KEYFILES_PATH, keyfile), ask_passwd()), False, None, "", True)
        if decrypted: return decrypted
        exit()
    print("Type the password to write into the encrypted file.")
    decrypted = confirm((lambda x :[decrypt(splitext(KEY_PATH)[0], x), x]), False, None, "", True, ask_passwd)
    if decrypted:
        data = json.load(open(KEY_PATH))
        with open(KEY_PATH, "w") as f: json.dump(data, f)
        encrypt(KEY_PATH, decrypted[1], splitext(KEY_PATH)[0])
        return
    exit()



def data_control(x: str = None, delete: bool = False, definitely: bool = False):
    try:
        data = json.load(open(KEY_PATH))
        if delete:
            if delete and not definitely:
                if not exists(TRASH_PATH):
                    with open(TRASH_PATH, "w") as f: f.write("{}")
                trash_data = json.load(open(TRASH_PATH))
                keyfile_name = basename(KEY_PATH) if splitext(basename(KEY_PATH))[1] != ".tmp" else splitext(basename(KEY_PATH))[0]
                if not f"{keyfile_name}" in trash_data: trash_data.update({f"{keyfile_name}": {}})
                keyfile = trash_data[f"{keyfile_name}"]
                keyfile.update({f"{len([i for i in keyfile])+1}": data[x]})
                with open(TRASH_PATH, "w") as f: json.dump(trash_data, f)
            data.pop(x)
        else: data.update(x)
        with open(KEY_PATH, "w") as f: json.dump(data, f)
        if KEY_PATH.endswith(".tmp"): encrypt_manager("w")
    except Exception as e: raise Exception(e)


def verify_json(list: bool = True):
    try:
        if exists(KEYFILES_PATH):
            dir_files = [f for f in listdir(KEYFILES_PATH) if f.endswith(".json") or f.endswith(".base64") and isfile(join(KEYFILES_PATH, f))]
            if len(dir_files) == 1: sort_ids()
            elif len(dir_files) > 1:
                global KEY_PATH
                if list:
                    dir_files.append("Exit")
                    q = inquirer.List("keyfile",message="Choice one of the key files", choices=dir_files, default="Exit"),
                    answer = inquirer.prompt(q)
                    if answer["keyfile"] == "Exit": exit()
                    keyfile = answer["keyfile"]
                else: keyfile = basename(KEY_PATH)
                if keyfile.endswith(".base64"):
                    decrypted = encrypt_manager("r", keyfile)
                    with open(join(KEYFILES_PATH, f"{keyfile}.tmp"), "wb") as f: f.write(decrypted)
                    keyfile = f"{keyfile}.tmp"
                KEY_PATH = join(KEYFILES_PATH, keyfile) 
                sort_ids()
            else:
                with open(KEY_PATH, "w") as f: f.write('{}')
        else:
            makedirs(KEYFILES_PATH)
            with open(KEY_PATH, "w") as f: f.write('{}')
    except Exception as e: raise Exception(e)


def get_table(header, time=False):
    data = json.load(open(KEY_PATH))
    if time: key_list = [[i, data[i]["name"], data[i]["issuer_name"], pyotp.TOTP(data[i]["key"]).now(), int(pyotp.TOTP(data[i]["key"]).interval\
                                                        - datetime.datetime.now().timestamp() % pyotp.TOTP(data[i]["key"]).interval)] for i in data]
    else: key_list = [[i, data[i]["name"], data[i]["issuer_name"], pyotp.TOTP(data[i]["key"]).now()] for i in data]
    if key_list != []: return tabulate(key_list,headers=header, tablefmt="fancy_grid")
    return False


def refresh_string(string):
    return '\033[F' * string.count("\n")


def time_left(totp):
    try:
        print("\nPress Ctrl+C to exit.\n")
        print(end="\n\n")
        while True:
            time_remaining = int(totp.interval - datetime.datetime.now().timestamp() % totp.interval)
            multi_line = f'Code: {totp.now()}\nTime left: {time_remaining} \n'
            print(f'{refresh_string(multi_line)}{multi_line}', end='')
            sleep(1)
    except KeyboardInterrupt: pass


#Typer commands

@app.command()
def show_code(
        key_id: str = typer.Argument(None, help="Key-ID to show code. (Use [command: keys] to see the IDs)"), 
        issuer: str = typer.Option(None, help="Search TOTP code by issuer."),
        e: bool = typer.Option(False, help="Show TOTP code of a key outside key file."),
        t: bool = typer.Option(False, help="Show the remaining time for the code to change.")
):
    try:
        if e:
            if key_id:
                totp = pyotp.TOTP(f'{key_id}')
                if t: time_left(totp)
                else: print(f"Code: {totp.now()}")
            else: print("Insert a key to show the code.")
            exit()
        verify_json()
        data = json.load(open(KEY_PATH))
        if issuer:
            matches = [i for i in data if data[i]["issuer_name"] == issuer]
            if len(matches) > 1:
                inquirer_list = [data[i]["name"] for i in matches]
                inquirer_list.append("Exit")
                q = inquirer.List("name",message="Choice one of the options to show the code", choices=inquirer_list, default="Exit"),
                answer = inquirer.prompt(q)
                if answer["name"] == "Exit": exit()
                answer = [i for i in matches if data[i]["name"] == answer["name"]]
                key_id = answer[0]
            elif len(matches) == 1: key_id = matches[0]
            else: print(f'Issuer "{issuer}" not in key file.')
        else:
            if data == {}:
                print("Theres no data in this key file.")
                exit()
            if key_id == None:
                raw_data = [[i, data[i]["name"], data[i]["issuer_name"]] for i in data]
                inquirer_list = [f"{i[1]}({i[2]})" for i in raw_data]
                inquirer_list.append("Exit")
                q = inquirer.List("choice",message="Choice one of the options to show the code", choices=inquirer_list, default="Exit"),
                answer = inquirer.prompt(q)
                if answer["choice"] == "Exit": exit()
                matches = [i[0] for i in raw_data if i[1] == answer["choice"].split("(", 1)[0] and i[2] == answer["choice"].split("(", 1)[1][:-1]]
                key_id = matches[0]
        if exists_in_json(key_id): 
            totp = pyotp.TOTP(data[key_id]["key"])
            if t: time_left(totp)
            else: print(f'{data[key_id]["name"]}({data[key_id]["issuer_name"]}) code: {totp.now()}')
        else:
            int(key_id)
            print(f'ID "{key_id}" not in key file.')
    except ValueError: raise ValueError("Key-ID must be an int.")
    except Exception as e: raise Exception(e)


@app.command()
def add_key(
        name: str = typer.Argument(help="Name, E-Mail, etc. Example = example@example.com"),
        issuer: str = typer.Argument(help="Issuer, provider, etc. Example = GitHub"),
        key: str = typer.Argument(help="Base32 key. Example = BASE32SECRET3232")
):
    try:
        verify_json()
        data = json.load(open(KEY_PATH))
        if exists_in_json(name, issuer, True): print(f"{name}({issuer}) already in key file.")
        else:
            new_data = {f"{len([i for i in data])+1}": {"name": f"{name}", "issuer_name": f"{issuer}", "key": f"{key}"}}
            data_control(new_data)
            print(f'{name}({issuer}) added to key file.')
    except Exception as e: raise Exception(e)


@app.command()
def del_key(
        key_id: str = typer.Argument(None, help="Key-ID to delete. Use [command: keys] to see IDs"), 
        issuer: str = typer.Option(None, help="Issuer, provider, etc. Example = GitHub"),
        d: bool = typer.Option(False, help="The eliminated key will be not redirected to the trash file and will be definitely eliminated.")
):
    try:
        verify_json()
        data = json.load(open(KEY_PATH))
        if issuer:    
            matches = [i for i in data if data[i]["issuer_name"] == issuer]
            if len(matches) > 1:
                inquirer_list = [data[i]["name"] for i in matches]
                inquirer_list.append("Exit")
                q = inquirer.List("name",message="Choice one of the options to delete", choices=inquirer_list, default="Exit"),
                answer = inquirer.prompt(q)
                if answer["name"] == "Exit": exit()
                key_id = [i for i in matches if data[i]["name"] == answer["name"]][0]
            elif len(matches) == 1: key_id = matches[0]
            else:
                print(f'Issuer "{issuer}" not in key file.')
                exit()
        else:
            if data == {}:
                print("There is no data in this key file.")
                exit()
            if key_id == None:
                raw_data = [[i, data[i]["name"], data[i]["issuer_name"]] for i in data]
                inquirer_list = [f"{i[1]}({i[2]})" for i in raw_data]
                inquirer_list.append("Exit")
                q = inquirer.List("choice",message="Choice one of the options to delete", choices=inquirer_list, default="Exit"),
                answer = inquirer.prompt(q)
                if answer["choice"] == "Exit": exit()
                matches = [i[0] for i in raw_data if i[1] == answer["choice"].split("(", 1)[0] and i[2] == answer["choice"].split("(", 1)[1][:-1]]
                key_id = matches[0]
        if exists_in_json(key_id):
            if confirm(lambda :input("Are you sure you wanna delete this key file? Y/N: ").lower(), "y", "n", "Insert a valid option."):
                if d: data_control(key_id, True, True)
                else: data_control(key_id, True)
                print(f'\n{data[key_id]["name"]}({data[key_id]["issuer_name"]}) removed from key file.\nUse [clean-trash] command to erase the key definitely '\
                                                                                                                'or [recover-key] command to recover the key.')
            else: exit()
        else:
            int(key_id)
            print(f'ID "{key_id}" not in key file.')
    except ValueError: raise ValueError("Key-ID must be a int.")
    except TypeError: raise TypeError("Key-ID must be a int.")
    except Exception as e: raise Exception(e)

@app.command()
def keys(t: bool = typer.Option(False, help="Show the remaining time for the codes to change.")):
    try:
        verify_json()
        if not get_table([""]):
            print("No keys in key file.")
            exit()
        if t:
            table = get_table([""])
            print("\nPress Ctrl+C to exit.\n")
            print("\n" * table.count("\n"), end="")
            while True:
                table = f'{get_table(["ID", "Name", "Issuer", "Code", "Time Remaining"], True)}\n'
                print(f'{refresh_string(table)}{table}', end='')
                sleep(1)
        table = get_table(["ID", "Name", "Issuer", "Code"])
        print(table)
    except Exception as e: raise Exception(e)
    except KeyboardInterrupt: pass


@app.command()
def gen_key(
        name: str = typer.Argument(None, help="Name, E-Mail, etc. Example = example@example.com"),
        issuer: str = typer.Argument(None, help="Issuer, provider, etc. Example = GitHub"),
        save: bool = typer.Option(False, help="Save the generated key in the key file."),
):
    try:
        key = pyotp.random_base32()
        if save and name and issuer: add_key(name, issuer, key)
        elif not save: print(f"New key: {key}")
        else: print("Please insert valid credentials.")
    except Exception as e: raise Exception(e)


@app.command()
def add_keyfile(
    name: str = typer.Argument(help="Name of the new key file."),
    encrypted: bool = typer.Option(False, help="Choose if the file is encrypted or not.")
):
    try:
        if encrypted:
            file = join(KEYFILES_PATH, f"{name}.base64")
            if exists(file): print("This key file already exists.")
            else:
                print("Enter the password for the new key file.\n(Type [G] in mayus to generate a random password)")
                passwd = ask_passwd(True)
                if type(passwd) == list: passwd = passwd[0]
                else:
                    print("\nVerify password.")
                    if not confirm(ask_passwd, passwd, None, "Password doesn't match, try again."): exit()
                with open(file, "w") as f: f.write("{}")
                encrypt(file, passwd, file)
                print(f'Key file: "{name}" created.')
        else:
            file = join(KEYFILES_PATH, f"{name}.json")
            if exists(file): print("This key file already exists.")
            else:
                with open(file, "w") as f: f.write("{}")
                print(f'Key file "{name}" created.')
    except Exception as e:
        raise Exception(e)


@app.command()
def del_keyfile(
    name: str = typer.Argument(None, help="Name of the key file you wanna delete.")
):
    try:
        file = None
        dir_files = [f for f in listdir(KEYFILES_PATH) if f.endswith(".json") or f.endswith(".base64") and isfile(join(KEYFILES_PATH, f))]
        if name:
            dir_files = [i for i in dir_files if name in i]
            if len(dir_files) == 1: file = join(KEYFILES_PATH, dir_files[0])
            elif len(dir_files) == 0:
                print(f"'{name}' doesn't exists.")
                exit()
        if not file:
            dir_files.append("Exit")
            q = inquirer.List("keyfile",message="Choice one of the key files to delete", choices=dir_files, default="Exit"),
            answer = inquirer.prompt(q)
            if answer["keyfile"] == "Exit": exit()
            file = join(KEYFILES_PATH, answer["keyfile"])
        if exists(file):
            if confirm(lambda :input("Are you sure you wanna delete this key file? Y/N: ").lower(), "y", "n", "Insert a valid option."): remove(file)
            else: exit()
    except Exception as e: raise Exception(e)


@app.command()
def encrypt_keyfile(
    name: str = typer.Argument(None, help="Name of the key file you wanna encrpyt.")
):
    if name:
        if f"{splitext(name)[1]}" == ".json": file = join(KEYFILES_PATH, name)
        else: file = join(KEYFILES_PATH, f"{splitext(name)[0]}.json")
    else:
        inquirer_list = [f for f in listdir(KEYFILES_PATH) if f.endswith(".json") and isfile(join(KEYFILES_PATH, f))]
        inquirer_list.append("Exit")
        q = inquirer.List("keyfile",message="Choice one of the key files to encrypt", choices=inquirer_list, default="Exit"),
        answer = inquirer.prompt(q)
        if answer["keyfile"] == "Exit": exit()
        file = join(KEYFILES_PATH, answer["keyfile"])
        name = answer["keyfile"]
    if exists(file):
        if exists(f"{splitext(file)[0]}.base64"):
            print("This file already have a encrypted version.")
            exit()
        print("Enter the password for the encrypted key file.\n(Type [G] in mayus to generate a random password)")
        passwd = ask_passwd(True)
        if type(passwd) == list: passwd = passwd[0]
        else:
            print("\nVerify password.")
            if not confirm(ask_passwd, passwd, None, "Password doesn't match, try again."): exit()
        encrypt(file, passwd, f"{splitext(file)[0]}.base64")
        print(f'Key file: "{name}" encrypted.')
        remove(file)
    else: print("This file doesn't exists.")


@app.command()
def mod_key(
    key_id: str = typer.Argument(None, help="Key-ID to modify. Use [command: keys] to see IDs"), 
    issuer: str = typer.Option(None, help="Issuer, provider, etc. Example = GitHub")
):
    try:
        verify_json()
        data = json.load(open(KEY_PATH))
        if issuer:    
            matches = [i for i in data if data[i]["issuer_name"] == issuer]
            if len(matches) == 1: key_id = matches[0]
            elif len(matches) == 0:
                print(f'Issuer "{issuer}" not in key file.')
                exit()
        if data == {}:
            print("Theres no data in this key file.")
            exit()
        if not key_id:
            if issuer:
                raw_data = [[i, data[i]["name"]] for i in data if data[i]["issuer_name"] == issuer]
                inquirer_list = [i[1] for i in raw_data]
            else:
                raw_data = [[i, data[i]["name"], data[i]["issuer_name"]] for i in data]
                inquirer_list = [f"{i[1]}({i[2]})" for i in raw_data]
            inquirer_list.append("Exit")
            q = inquirer.List("choice",message="Choice one of the keys to modify", choices=inquirer_list, default="Exit"),
            answer = inquirer.prompt(q)
            if answer["choice"] == "Exit": exit()
            if issuer: key_id = [i[0] for i in raw_data if answer["choice"] == i[1]][0]
            else: key_id = [i[0] for i in raw_data if i[1] == answer["choice"].split("(", 1)[0] and i[2] == answer["choice"].split("(", 1)[1][:-1]][0]
        if exists_in_json(key_id):
            print("\nLeave blank the spaces you dont wanna modify.\n")
            name = str(input("Insert new name: "))
            issuer_name = str(input("Insert new issuer: "))
            key = str(input("Insert new key (Type [G] to generate a new one): ")).upper()
            if key == "G": key = pyotp.random_base32()
            key = data[key_id]["key"] if key == "" else key
            name = data[key_id]["name"] if name == "" else name
            issuer_name = data[key_id]["issuer_name"] if issuer_name == "" else issuer_name
            if confirm(lambda :input("\nAre you sure you wanna modify this key file? Y/N: ").lower(), "y", "n", "Insert a valid option."):
                modified_key = {key_id: {"name": name, "issuer_name": issuer_name, "key": key}}
                data_control(modified_key)
                print(f"Changes done to the key file.")
            else: exit()
        else:
            int(key_id)
            print(f'ID "{key_id}" not in key file.')
    except ValueError: raise ValueError("Key-ID must be a int.")
    except TypeError: raise TypeError("Key-ID must be a int.")
    except Exception as e: raise Exception(e)


@app.command()
def clean_trash():
    try:
        if confirm(lambda :input("Are you sure you wanna delete all the keys stored in the trash file? Y/N: ").lower(), "y", "n", "Insert a valid option."):
            with open(TRASH_PATH, "w") as f: f.write("{}")
            print("Trash cleaned.")
    except Exception as e: raise Exception(e)


@app.command()
def recover_key(
    file: str = typer.Argument("", help="Name of the file. (Example: keys, keys.json, keys.base64...)")
):
    try:
        global KEY_PATH
        data = json.load(open(TRASH_PATH))
        keyfiles = [i for i in data]
        if f"{splitext(file)[1]}" == ".json" or f"{splitext(file)[1]}" == ".base64":
            if file:
                file = file
        else:
            if file:
                if len(keyfiles) == 1:
                    file = f"{splitext(file)[0]}.json"
                elif len(keyfiles) == 0:
                    if not exists(join(KEYFILES_PATH, file)):
                        print(f"The key file: '{file}' does not exists, you can create it with [add-keyfile] command.")
                        exit()
                    print("There is no keys of this key file in the trash file.")
            if len(keyfiles) == 1:
                file = keyfiles[0]
            elif len(keyfiles) == 0:
                print("The trash is empty.")
                exit()
            else:
                keyfiles.append("Exit")
                q = inquirer.List("keyfile",message="Choice one of the key files", choices=keyfiles, default="Exit"),
                answer = inquirer.prompt(q)
                if answer["keyfile"] == "Exit": exit()
                file = answer["keyfile"]
            KEY_PATH = join(KEYFILES_PATH, file)
        if not file in data:
            print("There is not keys of this key file in the trash.")
            exit()
        if not exists(KEY_PATH):
            print(f"The key file: '{file}' does not exists, you can create it with [add-keyfile] command.")
            exit()
        verify_json(False)
        raw_data = [[i, data[f"{file}"][i]["name"], data[f"{file}"][i]["issuer_name"]] for i in data[f"{file}"]]
        keys = [f"{i[1]}({i[2]})" for i in raw_data]
        if keys == []:
            print("The trash is empty.")
            exit()
        keys.append("Exit")
        q = inquirer.List("key",message="Choice one of the keys", choices=keys, default="Exit"),
        answer = inquirer.prompt(q)
        if answer["key"] == "Exit": exit()
        if confirm(lambda :input("Are you sure you wanna recover this key? (Y/N): "), "y", "n", "Insert a valid option."):
            key_id = [i[0] for i in raw_data if i[1] == answer["key"].split("(", 1)[0] and i[2] == answer["key"].split("(", 1)[1][:-1]][0]
        else: exit()
        name = data[f"{file}"][key_id]["name"]
        issuer = data[f"{file}"][key_id]["issuer_name"]
        key = data[f"{file}"][key_id]["key"]
        if exists_in_json(name, issuer, True):
            print(f"{name}({issuer}) already in key file, delete the one stored in the key file if you want this one.")
        else:
            keyfile_data = json.load(open(KEY_PATH))
            new_data = {f"{len([i for i in keyfile_data])+1}": {"name": f"{name}", "issuer_name": f"{issuer}", "key": f"{key}"}}
            old_data = data[f"{file}"]
            old_data.pop(key_id)
            if old_data == {}: data.pop(f"{file}")
            else: 
                sorted_ids = sort_ids(old_data, False)
                sorted_data = {f"{file}": sorted_ids}
                data.pop(f"{file}")
                data.update(sorted_data)
            with open(TRASH_PATH, "w") as f:
                f.write("")
                json.dump(data ,f)
            data_control(new_data)
    except Exception as e: raise Exception(e)


if __name__ == "__main__":
    register(exit_handler)
    app()
