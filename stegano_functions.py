"""Adapted code from x4nth055 (2019): 
https://github.com/x4nth055/pythoncode-tutorials/blob/master/ethical-hacking/
steganography/steganography.py
"""
import numpy as np
import PIL

def int2bin(number):
    """Convert number to binary format
    """
    return format(number, "08b");


def to_bin(data):
    """Convert "data" to binary format as string
    """
    if isinstance(data, str):
        return ''.join([ format(ord(i), "08b") for i in data ])
    elif isinstance(data, bytes) or isinstance(data, np.ndarray):
        return [ format(i, "08b") for i in data ]
    elif isinstance(data, int) or isinstance(data, np.uint8):
        return format(data, "08b")
    else:
        raise TypeError("Type not supported.")
        
        
def encode(original_image, secret_data, n_bits = 1, color_channels="RGB"):
    """ Function to encode a message string into an image.
        Parameters:
            original_image - Image that will be used for data encoding. 
                             Coming from PIL.Image.Open()
            secret_data - string to be encoded into the picture
            n_bits - how many last bits to be used for message encoding: 
                             default = 1
            color_channels - which color channels to be used for message 
                             encoding (options: "R", "G", "B", "RG","RB", "GB",
                            "RGB"): default = "RGB"
    return encoded image
    """
    
    # Use PIL Library to be compatible with wxPython bitmap.
    image = original_image.convert('RGB')
    pix = image.load()
    
    # Calculate maximum bytes to encode (subtract by 5 at end 
    #
    # due to ending "=====".
    n_bytes = (image.width * image.height * len(color_channels) 
               * n_bits // 8 - 5)     
    print("[*] Maximum bytes to encode:", n_bytes)
    
    # Crop  message so full picture is overlayed with secret message.
    secret_data = secret_data[0:n_bits * n_bytes]       
    
    print("[*] Encoding data...")
    
    # Add stopping criteria to tell if content of file has ended.
    secret_data += "====="  
    
    data_index = 0
    
    # Convert data to binary format.
    binary_secret_data = to_bin(secret_data) 
    
    # Calculate size of data to hide.
    data_len = len(binary_secret_data)
    
    # Collect RGB values of each pixel and convert to binary format.
    for col in range(image.height):
        for row in range(image.width):
            pixel = np.asarray(pix[row,col])
            r, g, b = to_bin(pixel) 
        
            if data_index < data_len and ("R" in color_channels.upper() ):
                # least significant red pixel bit
                temp_value_1 = (
                    r[:-n_bits] 
                    + binary_secret_data[data_index:data_index + n_bits])
                pixel[0] = int(temp_value_1, 2)
                data_index += n_bits
            
            if data_index < data_len and ("G" in color_channels.upper() ):
                # least significant green pixel bit
                temp_value_2 = (
                    g[:-n_bits] 
                    + binary_secret_data[data_index:data_index+n_bits])
                pixel[1] = int(temp_value_2, 2)
                data_index += n_bits
            
            if data_index < data_len and ("B" in color_channels.upper() ):
                # least significant blue pixel bit
                temp_value_3 = (
                    b[:-n_bits] 
                    + binary_secret_data[data_index:data_index+n_bits])
                pixel[2] = int(temp_value_3, 2)
                data_index += n_bits
                
            pix[row,col] = (pixel[0],pixel[1],pixel[2])
            
            # If data is encoded, break out of the loop.
            if data_index >= data_len:
                break
    return image


def decode(image_filepath, n_bits = 1, color_channels="RGB"):
    """ Function to decode a message string from an image.
        Parameters:
            image_filepath - file path of the image
            n_bits - how many last bits to be used for message encoding: 
                             default = 1
            color_channels - which color channels to be used for message 
                             encoding (options: "R", "G", "B", "RG","RB", "GB",
                            "RGB"): default = "RGB"
    return secret message
    """
    print("[+] Decoding ...")
    im = PIL.Image.open(image_filepath)
    pix = im.load()
    binary_data = ""
    for row in range(im.height):
        for col in range(im.width):
            pixel = np.asarray(pix[col,row])
            r, g, b = to_bin(pixel)
            if ("R" in color_channels.upper() ):
                binary_data += r[8-n_bits:8]
            if ("G" in color_channels.upper() ):
                binary_data += g[8-n_bits:8]
            if ("B" in color_channels.upper() ):
                binary_data += b[8-n_bits:8]
                
    # Split binary data by 8-bits.
    all_bytes = [binary_data[i: i+8] for i in range(0, len(binary_data), 8)]
    decoded_data = ""
    
    # Convert byte information to readable data.
    for byte in all_bytes:
        decoded_data += chr(int(byte, 2))
        if decoded_data[-5:] == "=====":
            break
    return decoded_data[:-5]