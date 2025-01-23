import binascii
import os
import tempfile


def save_file_in_pwd(data, file_name):
    try:
        # Get the current working directory
        current_directory = os.getcwd()

        # Construct the file path in the current directory
        file_path = os.path.join(current_directory, file_name)

        # Save the file
        with open(file_path, 'wb') as f_out:
            f_out.write(data)

        print(f"File saved successfully in the current working directory as: {file_path}")
    except IOError as e:
        print(f"Error saving file: {e}")
def bytes_to_hex(data):
    return data.hex()


def hex_to_bytes(hex_string):
    return bytes.fromhex(hex_string)


def divide_file(input_file, ext):
    # Open the original file for reading in binary mode
    # with open(input_file, 'rb') as f:
    #     content = f.read()

    # Calculate the size of each part
    total_size = len(input_file)
    part_size = total_size // 4

    # Divide the content into four parts
    parts = [input_file[i:i + part_size] for i in range(0, total_size, part_size)]
    # Determine the file extension
    # file_extension = input_file.split('.')[-1]

    # Create temporary files and write each part into a separate file
    output_files = []
    for i, part in enumerate(parts):
        _, output_file = tempfile.mkstemp(suffix=f'.{ext}')
        with open(output_file, 'wb') as f_out:
            f_out.write(part)
        output_files.append(output_file)

    return output_files


def bytes_to_hex(bytes_data):
    return binascii.hexlify(bytes_data).decode('utf-8')


def hex_to_bytes(hex_data):
    return binascii.unhexlify(hex_data)
