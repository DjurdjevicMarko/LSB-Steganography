import sewar_full_ref as sewar
import math
import numpy as np
from brisque import BRISQUE
from numpy import asarray
import skimage.measure


def get_psnr(mse):
    """Calculate the Peak signal-to-noise ratio (psnr)
    
        return psnr rounded to 3 decimal places
    """
    psnr = 20 * math.log(255/(math.sqrt(float(mse))), 10)
    return str(round(psnr,3))


def get_mse(original_image, encoded_image):
    """Calculate the Mean Squared Error (mse)
    
        return mse rounded to 3 decimal places
    """
    height = original_image.height
    width = original_image.width
    mse_sum = 0.0
    
    # Extract RGB values from each pixel in original and encoded image.
    for i in range(height):
        for j in range(width): 
            r1, g1, b1 = original_image.getpixel((j, i))
            r2, g2, b2 = encoded_image.getpixel((j, i))
            mse_sum += ((r1 - r2) ** 2) + ((g1 - g2) ** 2) + ((b1 - b2) ** 2)
    mse = mse_sum / (400 * 400 * 3)
    return str(round(mse,3))


def get_ssim(original_image, encoded_image):
    """Calculate the Structural similarity index measure (ssim)
    
        return ssim rounded to 3 decimal places
    """
    original_image = original_image.convert('RGB')
    encoded_image = encoded_image.convert('RGB')
    original_image_temp = np.array(original_image) 
    encoded_image_temp = np.array(encoded_image) 
    ssim, css = sewar.ssim(original_image_temp, encoded_image_temp)
    return str(round(ssim,3))


def get_entropy(image):
    """Calculate the entropy
    
        return entropy rounded to 3 decimal places
    """
    entropy = skimage.measure.shannon_entropy(image)
    return str(round(entropy,3))


def get_brisque(image):
    """Calculate the BRISQUE Score
    
        return BRISQUE Score rounded to 3 decimal places
    """
    numpydata = asarray(image)
    object = BRISQUE(url=False)
    result = object.score(numpydata)
    return str(float(round(result, 3)))