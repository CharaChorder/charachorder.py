from .device import CharaChorder


def main():
    for device in CharaChorder.list_devices():
        with device:
            print(device.execute("ID"))


if __name__ == "__main__":
    main()
