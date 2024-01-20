from .device import CharaChorder
from .errors import UnknownCommand


def charachorder_shell(device: CharaChorder) -> None:
    print(f"{device.get_id()} ({device.connection.port})")
    print(f"CCOS {device.get_version()}")

    while True:
        try:
            command = input("> ").split(" ")

            try:
                result = device._execute(" ".join(command))
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
        print("Too many devices connected to spawn a shell.")
