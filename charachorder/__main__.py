import inquirer

from .device import CharaChorder
from .errors import UnknownCommand


def charachorder_shell(device: CharaChorder) -> None:
    print(f"{device.get_id()} ({device.connection.port})")
    version = device.get_version()
    print("CCOS" if version[0] == "1" else "Firmware version", version)

    while True:
        try:
            command = input("> ").split(" ")

            try:
                result = device._execute(*command)
                print(" ".join(result))
            except UnknownCommand:
                print("Unknown command. For a list of available commands, run `CMD`")
        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    devices = CharaChorder.list_devices()
    if len(devices) == 0:
        print("No CharaChorder devices found.")
    elif len(devices) == 1:
        with devices[0]:
            charachorder_shell(devices[0])
    else:
        question = inquirer.List(
            "device",
            message="Please choose one of the connected devices",
            choices=[*devices, *devices],
            carousel=True,
        )
        if answers := inquirer.prompt(
            [question],
            theme=inquirer.themes.load_theme_from_dict(
                {"List": {"selection_cursor": "->"}}
            ),
        ):
            selected_device = answers["device"]
            with selected_device:
                charachorder_shell(selected_device)
