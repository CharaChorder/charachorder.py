import charachorder
import inquirer


def charachorder_shell(device: charachorder.CharaChorder) -> None:
    print(f"{device.get_id()} ({device.connection.port})")
    version = device.get_version()
    print("Firmware version" if version[0] == "0" else "CCOS", version)

    while True:
        try:
            command = [word for word in input("> ").split(" ") if word]
            if not command:
                continue
            if command[0] == "exit":
                break

            try:
                result = device._execute(*command)
                print(" ".join(result))
            except charachorder.UnknownCommand:
                print("Unknown command. For a list of available commands, run `CMD`")
        except KeyboardInterrupt:
            print()
            continue
        except EOFError:
            print()
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    devices = charachorder.CharaChorder.list_devices()
    if len(devices) == 0:
        print("No CharaChorder devices found.")
    elif len(devices) == 1:
        with devices[0]:
            charachorder_shell(devices[0])
    else:
        question = inquirer.List(
            "device",
            message="Please choose one of the connected devices",
            choices=devices,
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
