import uos



def list_files_recursive(path):
    try:
        items = uos.listdir(path)
    except OSError:
        return

    for item in items:
        item_path = '{}/{}'.format(path, item)
        try:
            if uos.stat(item_path)[0] == 0o100000:
                print(item_path)
            else:
                list_files_recursive(item_path)
        except OSError:
            pass



current_directory = uos.getcwd()
list_files_recursive(current_directory)