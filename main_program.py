import math
import wx
import skimage.measure
import os
import openpyxl
import pandas as pd
import numpy as np
import stegano_functions as stegano 
import sewar_full_ref as sewar
import stegano_statistics as statistics
from PIL import Image
from brisque import BRISQUE
from numpy import asarray


""" ACTIVATE_BUTTON can be either set to True or False.
    True -  No GUI, Images in IMAGES_FOLDER get encoded with parameters: 
            COLOUR_CHANNELS_LIST and BIT_DEPTH_LIST where the results are 
            transferred to EXCEL_FILE
    False - GUI, Import button to import images, no transferring of results
"""

ACTIVATE_BUTTON = False

### Change the following parameters if ACTIVATE_BUTTON = True

# Folder path containing images for encoding.
IMAGES_FOLDER = "C:\\[example]\ImagesToEncode"

# Folder path where encoded images are saved
OUTPUT_DIRECTORY = r'C:\\[example]\encoded_images'

# File path of Excel file where data will be transferred
EXCEL_FILE = "C:\\Users\[example]\image_quality_results.xlsx"   

# List of colour channels to be encoded
COLOUR_CHANNELS_LIST = ["RGB","R", "G", "B", "RG", "RB", "GB"]

# List of bit depths which will be analyzed
BIT_DEPTH_LIST = [1, 2, 3, 4, 5, 6, 7] 

HELP_MESSAGE = """
Here are the following steps required to use this steganography tool.
                       
    1. Press the import button and choose an image 
    of PNG or JPEG format

    2. If desired, change the colour space and number of bits to be used 
    in the encoding process

    3. If desired, save the encoded image by 
    pressing the "Save Encoded Image" button and  
    selecting a file location
    """     

class GuiCompareDialog(wx.Dialog):
    """Create GUI with wx.Dialog. Includes image comparison, button binding, 
        event handling and calculation of image quality measures.
    
        The visual aspect of the GUI was done with wxGlade.
    """
    def __init__(self, *args, **kwds):
        """Design GUI (wxGlade) and bind buttons with event handling.
        """
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_DIALOG_STYLE
        wx.Dialog.__init__(self, *args, **kwds)
        
        # Set title name and size.
        self.SetSize((1200, 650))
        self.SetTitle("Marko's Steganography Tool")

        sizer_main = wx.BoxSizer(wx.VERTICAL)
        sizer_top_title = wx.BoxSizer(wx.HORIZONTAL)
        sizer_main.Add(sizer_top_title, 0, wx.EXPAND, 0)
        
        # Add a spacer before title of the window.
        sizer_top_title.Add((150, 20), 0, 0, 0)    
        
        title = wx.StaticText(
            self, wx.ID_ANY, "Steganography Image Comparison", 
            style=wx.ALIGN_CENTER_HORIZONTAL)
        
        title.SetFont(
            wx.Font(13, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, 
                    wx.FONTWEIGHT_BOLD, 0, ""))
        
        sizer_top_title.Add(title, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        
        # Add a spacer between the title and help button.
        sizer_top_title.Add((550, 20), 0, 0, 0)      

        self.help_button = wx.Button(self, wx.ID_ANY, 
                                    "Help", style=wx.BORDER_NONE)
        
        sizer_top_title.Add(self.help_button, 0,
                           wx.ALIGN_CENTER_VERTICAL | wx.ALL, 15)
        self.help_button.Bind(wx.EVT_BUTTON, self.on_help_click)

        sizer_middlepart_titles = wx.BoxSizer(wx.HORIZONTAL)
        sizer_main.Add(sizer_middlepart_titles, 0, wx.EXPAND, 0)

        original_image_statictext = wx.StaticText(
            self, wx.ID_ANY, "Original Image", 
            style=wx.ALIGN_CENTRE_HORIZONTAL, size=(400,20))
        
        original_image_statictext.SetForegroundColour("blue")
        original_image_statictext.SetFont(
            wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, 
            wx.FONTWEIGHT_BOLD, 0, ""))
        sizer_middlepart_titles.Add(original_image_statictext, 0, 
                                    wx.LEFT | wx.TOP, 30)

        encoded_image_statictext = wx.StaticText(
          self, wx.ID_ANY, "Encoded Image", 
          style=wx.ALIGN_CENTRE_HORIZONTAL, size=(400,20))
        
        encoded_image_statictext.SetForegroundColour("brown")
        
        encoded_image_statictext.SetFont(
            wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, 
                    wx.FONTWEIGHT_BOLD, 0, ""))
        
        sizer_middlepart_titles.Add(encoded_image_statictext, 0, 
                                    wx.RIGHT|wx.TOP,30)

        self.statistics_statictext = wx.StaticText(
          self, wx.ID_ANY, "Statistics", 
          style=wx.ALIGN_CENTRE_HORIZONTAL, size=(400,20))
        
        self.statistics_statictext.SetBackgroundColour("grey")
        self.statistics_statictext.SetForegroundColour("white")
        self.statistics_statictext.SetFont(
          wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, 
                  wx.FONTWEIGHT_BOLD, 0, ""))
        
        sizer_middlepart_titles.Add(self.statistics_statictext, 0, 
                                    wx.RIGHT | wx.TOP, 30)

        sizer_middlepart_images = wx.BoxSizer(wx.HORIZONTAL)
        sizer_main.Add(sizer_middlepart_images, 1, wx.ALIGN_LEFT, 0)
        
        # Add a spacer before the original image.
        sizer_middlepart_images.Add((5, 400), 0, 0, 0)        
        
        self.original_image_bitmap = wx.StaticBitmap(
          self, wx.ID_ANY, 
          wx.Bitmap("original_placeholder.png", wx.BITMAP_TYPE_ANY))
        
        self.original_image_bitmap.SetMinSize((400, 400))
        
        sizer_middlepart_images.Add(
          self.original_image_bitmap, 0, 
          wx.ALL | wx.RESERVE_SPACE_EVEN_IF_HIDDEN , 0)
        
        # Add a spacer between the original and encoded image. 
        sizer_middlepart_images.Add((5, 400), 0, 0, 0)
        
        self.encoded_image_bitmap = wx.StaticBitmap(
          self, wx.ID_ANY, 
          wx.Bitmap("encoded_placeholder.png", wx.BITMAP_TYPE_ANY))
        
        self.encoded_image_bitmap.SetMinSize((400, 400))
        
        sizer_middlepart_images.Add(
          self.encoded_image_bitmap, 0, 
          wx.ALL | wx.RESERVE_SPACE_EVEN_IF_HIDDEN , 0)

        grid_sizer_statistics = wx.GridSizer(6, 2, 0, 0)
        sizer_middlepart_images.Add(grid_sizer_statistics, 1, wx.EXPAND, 0)
        grid_sizer_statistics.Add((0, 0), 0, 0, 0)

        encoded_label_statictext = wx.StaticText(
          self, wx.ID_ANY, "encoded",
          style=wx.ALIGN_CENTRE_HORIZONTAL, size=(150,20))
        
        encoded_label_statictext.SetFont(
          wx.Font(10, wx.FONTFAMILY_ROMAN, wx.FONTSTYLE_NORMAL, 
                  wx.FONTWEIGHT_BOLD, 0, ""))
        
        encoded_label_statictext.SetForegroundColour("brown")
        grid_sizer_statistics.Add(encoded_label_statictext, 0, 
                                  wx.ALIGN_CENTER, 0)
    
        # PSNR Statistics
        psnr_statictext = wx.StaticText(self, wx.ID_ANY, "PSNR")
        psnr_statictext.SetFont(
          wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL, 
                  wx.FONTWEIGHT_NORMAL, 0, ""))
        
        grid_sizer_statistics.Add(psnr_statictext, 0, wx.ALIGN_CENTER, 0)
        
        self.psnr_result_statictext = wx.StaticText(self, wx.ID_ANY, "no data")
        grid_sizer_statistics.Add(self.psnr_result_statictext, 
                                  0, wx.ALIGN_CENTER, 0)
        
        # MSE Statistics
        mse_statictext = wx.StaticText(self, wx.ID_ANY, "MSE")
        mse_statictext.SetFont(
          wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL,
                  wx.FONTWEIGHT_NORMAL, 0, ""))
        
        grid_sizer_statistics.Add(mse_statictext, 0, wx.ALIGN_CENTER, 0)

        self.mse_result_statictext = wx.StaticText(self, wx.ID_ANY, "no data")
        grid_sizer_statistics.Add(self.mse_result_statictext, 0, 
                                  wx.ALIGN_CENTER, 0)

        # SSIM Statistics
        ssim_statictext = wx.StaticText(self, wx.ID_ANY, "SSIM")
        ssim_statictext.SetFont(
          wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL,
                  wx.FONTWEIGHT_NORMAL, 0, ""))
        
        grid_sizer_statistics.Add(ssim_statictext, 0, wx.ALIGN_CENTER, 0)

        self.ssim_result_statictext = wx.StaticText(self, wx.ID_ANY, "no data")
        grid_sizer_statistics.Add(self.ssim_result_statictext, 0,
                                  wx.ALIGN_CENTER, 0)
        
        # entropy Statistics
        entropy_statictext = wx.StaticText(self, wx.ID_ANY, "Entropy")
        entropy_statictext.SetFont(
          wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL,
                  wx.FONTWEIGHT_NORMAL, 0, ""))
        
        grid_sizer_statistics.Add(entropy_statictext, 0, wx.ALIGN_CENTER, 0)

        self.entropy_result_statictext = wx.StaticText(self, wx.ID_ANY, 
                                                       "no data")
        grid_sizer_statistics.Add(self.entropy_result_statictext, 0,
                                  wx.ALIGN_CENTER, 0)

        # BRISQUE Statistics
        brisque_statictext = wx.StaticText(self, wx.ID_ANY, "BRISQUE")
        brisque_statictext.SetFont(
          wx.Font(10, wx.FONTFAMILY_MODERN, wx.FONTSTYLE_NORMAL,
                  wx.FONTWEIGHT_NORMAL, 0, ""))
        
        grid_sizer_statistics.Add(brisque_statictext, 0, wx.ALIGN_CENTER, 0)

        self.brisque_result_statictext = wx.StaticText(self, wx.ID_ANY, 
                                                       "no data")
        grid_sizer_statistics.Add(self.brisque_result_statictext, 0, 
                                  wx.ALIGN_CENTER, 0)
        
        sizer_lowerpart_buttons = wx.BoxSizer(wx.HORIZONTAL)
        sizer_main.Add(sizer_lowerpart_buttons, 1, wx.TOP, 0)
        
        # Add a spacer before import button.
        sizer_lowerpart_buttons.Add((50, 1), 0, 0, 0) 
        
        # Import Button
        self.import_button = wx.Button(self, wx.ID_ANY, "Import Image")
        self.import_button.SetMinSize((150, 35))
        sizer_lowerpart_buttons.Add(self.import_button, 0, 
                                    wx.ALIGN_CENTER_VERTICAL | wx.ALL, 14)
        self.import_button.Bind(wx.EVT_BUTTON, self.on_open_file)
        
        # Save Button
        self.save_button = wx.Button(self, wx.ID_ANY, 
                                    "Save Encoded Image", style=wx.BORDER_NONE)
        self.save_button.SetMinSize((150, 35))
        sizer_lowerpart_buttons.Add(self.save_button, 0, 
                                    wx.ALIGN_CENTER_VERTICAL | wx.ALL, 15) 
        
        # The default is off and enables once the encoded image is loaded.
        self.save_button.Enable(False)      
        self.save_button.Bind(wx.EVT_BUTTON, self.save_encoded_image_bitmap)
    
        # Bits Slider
        bits_to_encode_statictext = wx.StaticText(self, wx.ID_ANY,
                                                  "Bits to encode:")
        sizer_lowerpart_buttons.Add(bits_to_encode_statictext, 0, 
                                    wx.ALIGN_CENTER_VERTICAL, 0)
        
        # The default is 4 and the range is 1 - 7.
        self.number_bits_slider = wx.Slider(
          self, wx.ID_ANY, 4, 1, 7, 
          style=wx.SL_VALUE_LABEL | wx.SL_AUTOTICKS)
        
        sizer_lowerpart_buttons.Add(self.number_bits_slider, 0,
                                    wx.ALIGN_CENTER_VERTICAL, 0)
        self.number_bits_slider.Bind(wx.EVT_SCROLL_THUMBRELEASE, 
                                     self.on_n_bits_change)
        
        #Add a spacer between the bits slider and colour channels.
        sizer_lowerpart_buttons.Add((3, 20), 0, 0, 0) 
        
        # Colour Channels
        colour_channels_statictext = wx.StaticText(self, wx.ID_ANY, 
                                                   "Colour Channels:")
        sizer_lowerpart_buttons.Add(colour_channels_statictext, 0, 
                                    wx.ALIGN_CENTER_VERTICAL, 0)
    
        self.red_colour_channel = wx.CheckBox(self, wx.ID_ANY,
                                            "R ", style=wx.ALIGN_RIGHT)
        self.red_colour_channel.SetMinSize((30, 23))
        self.red_colour_channel.SetBackgroundColour("red")
        
        # The default is true and can be set to false upon unticking checkbox.
        self.red_colour_channel.SetValue(True) 
        self.red_colour_channel.Bind(wx.EVT_CHECKBOX, self.on_RGB_change)
        
        sizer_lowerpart_buttons.Add(self.red_colour_channel, 0, 
                                    wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_lowerpart_buttons.Add((3, 20), 0, 0, 0)

        self.green_colour_channel = wx.CheckBox(self, wx.ID_ANY, 
                                              "G", style=wx.ALIGN_RIGHT)
        self.green_colour_channel.SetMinSize((30, 23))
        self.green_colour_channel.SetBackgroundColour("green")
        
        # The default is true and can be set to false upon unticking checkbox.
        self.green_colour_channel.SetValue(True)
        self.green_colour_channel.Bind(wx.EVT_CHECKBOX, self.on_RGB_change)
        
        sizer_lowerpart_buttons.Add(self.green_colour_channel, 0, 
                                    wx.ALIGN_CENTER_VERTICAL | wx.ALL, 0)
        sizer_lowerpart_buttons.Add((3, 20), 0, 0, 0)

        self.blue_colour_channel = wx.CheckBox(self, wx.ID_ANY, 
                                             "B", style=wx.ALIGN_RIGHT)
        self.blue_colour_channel.SetMinSize((30, 23))
        self.blue_colour_channel.SetBackgroundColour("blue")
        
        # The default is true and can be set to false upon unticking checkbox.
        self.blue_colour_channel.SetValue(True)
        self.blue_colour_channel.Bind(wx.EVT_CHECKBOX, self.on_RGB_change)
        
        sizer_lowerpart_buttons.Add(self.blue_colour_channel, 0, 
                                    wx.ALIGN_CENTER_VERTICAL, 0)

        self.SetSizer(sizer_main)
        
        # Close the interface upon the user exiting.
        self.Bind(wx.EVT_CLOSE, self.on_close)

        self.Layout()
        
        # End of wxGlade.
        self.psnr_perceptible = 0
        self.mse_perceptible = 0
        self.ssim_perceptible = 0
        self.entropy_perceptible = 0
        self.brisque_perceptible = 0

    def get_colour_space(self):
        """ Check which colour channel checkboxes are ticked in GUI
        
            return colour space
        """
        colour_space = ""
        
        # If the red colour channel checkbox is ticked, use it for embedding.
        if (self.red_colour_channel.Value == True): 
            colour_space = colour_space + "R"
            
        # If the green colour channel checkbox is ticked, use it for embedding.
        if (self.green_colour_channel.Value == True):
            colour_space = colour_space + "G"
            
        # If the blue colour channel checkbox is ticked, use it for embedding.
        if (self.blue_colour_channel.Value == True):
            colour_space = colour_space + "B"    
            
        # If no checkbox is ticked, choose RGB as the default colour space.
        if (colour_space == ""): 
            colour_space = "RGB"
            
        return colour_space
    
    def get_statistics_mse(self):
        """Calculate the Mean Squared Error (mse)
        
            return mse rounded to 3 decimal places
        """
        height = self.original_image.height
        width = self.original_image.width
        mse_sum = 0.0
        
        for i in range(height):
            for j in range(width): 
                # Extract the RGB values from each pixel in the original image
                #
                # and encoded image.
                r1, g1, b1 = self.original_image.getpixel((j, i)) 
                r2, g2, b2 = self.encoded_image.getpixel((j, i))
                
                mse_sum += ((r1 - r2) ** 2) + ((g1 - g2) ** 2) 
                + ((b1 - b2) ** 2)
                
        mse = mse_sum / (400 * 400 * 3)
        
        return str(round(mse, 3))
    
    def get_statistics_psnr(self, mse):
        """Calculate the Peak signal-to-noise ratio (psnr)
        
            return psnr rounded to 3 decimal places
        """
        psnr = 20 * math.log(255/(math.sqrt(float(mse))), 10)
        return str(round(psnr, 3))
    
    def get_statistics_ssim(self):
        """Calculate the Structural similarity index measure (ssim)
        
            return ssim rounded to 3 decimal places
        """
        ssim, css = sewar.ssim(self.original_image_temp, self.encoded_image_temp) 
        return str(round(ssim, 3))

    def get_statistics_entropy(self, image):
        """Calculate the entropy
        
            return entropy rounded to 3 decimal places
        """
        entropy = skimage.measure.shannon_entropy(image)
        return float(round(entropy, 3))

    def get_statistics_brisque(self, image):
        """Calculate the BRISQUE Score
        
            return BRISQUE Score rounded to 3 decimal places
        """
        numpydata = asarray(image)
        object = BRISQUE(url=False)
        result = object.score(numpydata)
        return float(round(result, 3))
           
    def on_open_file(self, event):
        """ Retrieve image file path from importing button and show image 
            in GUI.
        """
        dialog = wx.FileDialog(self, message="Select a file", wildcard="", 
                               style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)
        
        if dialog.ShowModal() == wx.ID_OK:
            self.image_path = dialog.GetPath()
            self.path_temp = self.image_path
            self.original_image = wx.Image(self.image_path, wx.BITMAP_TYPE_ANY)
            
            bitmap = wx.Bitmap(self.original_image)
            
            # Show the original image on screen.
            self.original_image_bitmap.SetBitmap(bitmap) 
            
            # Convert the image from RGBA format to RGB format.
            self.original_image = Image.open(self.image_path).convert("RGB")  
            
            # Convert to numPy format to be compatible with ssim formula.
            self.original_image_temp = np.array(self.original_image)  
 
            # Upon opening an image, the save button becomes usable.
            self.save_button.Enable(True)
            
            self.show_images()

        dialog.Destroy()
        
    def on_n_bits_change(self, event):
        """ After moving the bits slider, call the show_images() function
            where the encoded image and statistics will be updated.
        """
        self.show_images()
        
    def on_RGB_change(self, event):
        """ After ticking/unticking a colour channel checkbox, call the 
            show_images() function where the encoded image and statistics will 
            be updated.
        """
        self.show_images()

    def on_close(self, event):
        """Destroy dialog after closing.
        """
        self.Destroy()

    def on_help_click(self, event):
        """Display help message if help button is clicked.
        """
        dlg = wx.MessageDialog(self, HELP_MESSAGE)

        dlg.ShowModal()
        dlg.Destroy()
        

    def scale_to_fit(self, Image):
        """Scale image to fit in dialog.
        """
        width, height = (400, 400)
        initial_width, initial_height = Image.GetSize()

        aspect = initial_height / initial_width
        
        new_width = width
        new_height = int(new_width * aspect)

        if new_height > height:
            new_height = height
            new_width = int(new_height / aspect)

        return Image.Rescale(wx.Size(new_width,new_height))

    def save_encoded_image_bitmap(self, event):
        """"Save encoded image if "Save Encoded Image" button is pressed.
        """
        dialog = wx.FileDialog(
          self, message="Select a file", 
          wildcard="Image files (*.png, *.jpg)|*.png;*.jpg|All Files|*.*", 
          style=wx.FD_SAVE)

        if dialog.ShowModal() == wx.ID_OK:
            self.image_path = dialog.GetPath()
            self.encoded_image.save(self.image_path)
            dlg = wx.MessageDialog(self, "File Saved to " + self.image_path, 
                                   "Save Completed")
            dlg.ShowModal()
            dlg.Destroy()

        dialog.Destroy()
     
    def show_images(self): 
        """Refresh GUI after moving bits slider or ticking/unticking colour
           channel checkbox. Display new encoded image and update statistics.
        """
        colour_space = self.get_colour_space()

        # Encode image with user-chosen parameters.
        self.encoded_image = stegano.encode(
          self.original_image, contents, 
          self.number_bits_slider.Value, colour_space) 
        
        # Convert to numPy format to be compatible with ssim formula.
        self.encoded_image_temp = np.array(self.encoded_image)
        
        height = self.encoded_image.height
        width = self.encoded_image.width
        
        ### Retrieve the results from Image Quality Measures.
        # MSE
        self.mse_result = self.get_statistics_mse()
        
        # This is the range concluded from results of experiment.
        if float(self.mse_result) >= 206.13825:
            # Set background colour to red.
            self.mse_result_statictext.SetBackgroundColour((255, 0, 
                                                            0, 255)) 
        elif float(self.mse_result) < 206.13825 and (float(self.mse_result) 
                                                     >= 7.1765):
            self.mse_perceptible = 1
            # Set background colour to yellow.
            self.mse_result_statictext.SetBackgroundColour((255, 255, 
                                                             0, 255))
        else:
            # Set background colour to green.
            self.mse_result_statictext.SetBackgroundColour((0, 255, 
                                                            0, 255)) 
        self.mse_result_statictext.SetLabel(self.mse_result)
 
        # PSNR
        psnr_result = self.get_statistics_psnr(self.mse_result)
        
        # This is the range concluded from results of experiment.
        if float(psnr_result) <= 25.0985:
            self.psnr_perceptible = 1
            # Set background colour to red.
            self.psnr_result_statictext.SetBackgroundColour((255, 0, 
                                                             0, 255))
        elif float(psnr_result) <= 39.6945 and float(psnr_result) > 25.0985:
            self.psnr_perceptible = 1
            # Set background colour to yellow.
            self.psnr_result_statictext.SetBackgroundColour((255, 255, 
                                                             0, 255))
        else:
            self.psnr_perceptible = 0
            # Set background colour to green.
            self.psnr_result_statictext.SetBackgroundColour((0, 255, 
                                                             0, 255))
        self.psnr_result_statictext.SetLabel(psnr_result)
        
        # SSIM
        ssim_result = self.get_statistics_ssim()
        
        # This is the range concluded from results of experiment.
        if float(ssim_result) <= 0.80291:
            self.ssim_perceptible = 1
            # Set background colour to red.
            self.ssim_result_statictext.SetBackgroundColour((255, 0, 
                                                             0, 255))
        elif float(ssim_result) <= 0.9865 and float(ssim_result) > 0.80291:
            self.ssim_perceptible = 1
            # Set background colour to yellow.
            self.ssim_result_statictext.SetBackgroundColour((255, 255, 
                                                             0, 255))
        else:
            self.ssim_perceptible = 0
            # Set background colour to green.
            self.ssim_result_statictext.SetBackgroundColour((0, 255, 
                                                             0, 255))
        self.ssim_result_statictext.SetLabel(ssim_result)
        
        # Entropy
        entropy_result_original_image = self.get_statistics_entropy(
          self.original_image)
        entropy_result_encoded_image = self.get_statistics_entropy(
          self.encoded_image)
        delta_entropy_result = math.sqrt((entropy_result_original_image 
                                    - entropy_result_encoded_image)**2)
        
        # This is the range concluded from results of experiment.
        if float(delta_entropy_result) > 0.02975:
            self.entropy_perceptible = 1
            # Set background colour to red.
            self.entropy_result_statictext.SetBackgroundColour((255, 0, 
                                                             0, 255))
        else:
            self.entropy_perceptible = 0
            # Set background colour to green.
            self.entropy_result_statictext.SetBackgroundColour((0, 255, 
                                                                0, 255))
        
        concatenate_temp = (str(entropy_result_original_image) 
                            + "       " + str(entropy_result_encoded_image))
        self.entropy_result_statictext.SetLabel(concatenate_temp)
        
        # BRISQUE
        brisque_result_original_image = self.get_statistics_brisque(
          self.original_image)
        brisque_result_encoded_image = self.get_statistics_brisque(
          self.encoded_image)
        delta_brisque_result = math.sqrt((brisque_result_original_image 
                                   - brisque_result_encoded_image)**2)
        
        # This is the range concluded from results of experiment.
        if float(delta_brisque_result) >= 22.79:
            self.brisque_perceptible = 1
            # Set background colour to red.
            self.brisque_result_statictext.SetBackgroundColour((255, 0, 
                                                                0, 255))
        elif (float(delta_brisque_result) >= 6.309 
              and float(delta_brisque_result) < 22.79):
            self.brisque_perceptible = 1
            # Set background colour to yellow.
            self.brisque_result_statictext.SetBackgroundColour((255, 255, 
                                                                0, 255))
        else:
            self.brisque_perceptible = 0
            # Set background colour to green.
            self.brisque_result_statictext.SetBackgroundColour((0, 255, 
                                                                0, 255))
            
        concatenate_temp = (str(brisque_result_original_image) + "       " 
                            + str(brisque_result_encoded_image))
        self.brisque_result_statictext.SetLabel(concatenate_temp)
    
        # Decide combined value from all 5 measures if overall results is 
        #
        # perceptible.
        sum_measures_perceptible = (self.psnr_perceptible 
          + self.mse_perceptible + self.ssim_perceptible 
          + self.entropy_perceptible + self.brisque_perceptible)
        
        if sum_measures_perceptible < 3:
            self.statistics_statictext.SetBackgroundColour("dark green")
            self.statistics_statictext.SetLabel("Statistics (Good!)")
        elif sum_measures_perceptible == 3:
            self.statistics_statictext.SetBackgroundColour("orange")
            self.statistics_statictext.SetLabel("Statistics (?)")
        else: 
            self.statistics_statictext.SetBackgroundColour("red")
            self.statistics_statictext.SetLabel("Statistics (Bad!)")
        
        image = wx.Image(width, height)
        image.SetData(self.encoded_image.tobytes())
        wx_bitmap = image.ConvertToBitmap()   
        self.encoded_image_bitmap.SetBitmap(wx_bitmap)
        self.Layout()

class GuiCompareApp(wx.App):
    def OnInit(self):
        """Initialize GuiCompareDialog.
        """
        self.dialog = GuiCompareDialog(None, wx.ID_ANY, "")
        self.SetTopWindow(self.dialog)
        self.dialog.ShowModal()
        
        return True
    
    def ShowDialog(self):
        """Show GuiCompareDialog.
        """
        self.SetTopWindow(self.dialog)
        self.dialog.ShowModal()

        return True

def excel_data_transfer():
    """Transfer results to Excel File.
    """
    # Create list of all image paths in IMAGES_FOLDER folder.
    image_paths = []
    for root, dirs, files in os.walk(IMAGES_FOLDER):
        for file in files:
            if file.endswith((".jpg", ".jpeg", ".png")):
                image_path = os.path.join(root, file)
                image_paths.append(f"{image_path}")
                
    colour_combinations = COLOUR_CHANNELS_LIST
    bit_depths = BIT_DEPTH_LIST
    results = []
    
    for colour_combination in colour_combinations:
        for bit_depth in bit_depths:
            for file in image_paths:
                original_image = Image.open(str(file))
                print(file, "+ processing bit depth =",bit_depth, 
                      " colour channel/s =",colour_combination)
                
                # Encode the image with each combination of parameters.
                encoded_image = stegano.encode(original_image, contents, 
                                               bit_depth, colour_combination)

                # Calculate image quality measures.
                mse = statistics.get_mse(original_image, encoded_image)
                psnr = statistics.get_psnr(mse)
                ssim = statistics.get_ssim(original_image, encoded_image)
                entropy_original = statistics.get_entropy(original_image)
                entropy_encoded = statistics.get_entropy(encoded_image)
                brisque_original = statistics.get_brisque(original_image)
                brisque_encoded = statistics.get_brisque(encoded_image)
    
                # Create a result entry with statistics and image details.
                result_entry = {
                    "ImageFile": file,
                    "ColourCombination": colour_combination,
                    "BitDepth": bit_depth,
                    "PSNR": psnr,
                    "MSE": mse,
                    "SSIM": ssim,
                    "EntropyOriginal": entropy_original,
                    "EntropyEncoded": entropy_encoded,
                    "BrisqueOriginal": brisque_original,
                    "BrisqueEncoded": brisque_encoded,
                }
                
                results.append(result_entry)
                
                filename = os.path.basename(file)
                
                # If the image is PNG format, save the encoded image as PNG.
                if file[-3:] == "png": 
                    output_filename = (
                      f"{filename}_{colour_combination}_{bit_depth}.png")
                    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    
                    # Save the image to the specified path
                    output_path = os.path.join(OUTPUT_DIRECTORY, 
                                               output_filename)
                    encoded_image.save(output_path)
                    
                # If the image is JPG format, save the encoded image as JPG.
                elif file[-3:] == "jpg":
                        output_filename = (
                          f"{filename}_{colour_combination}_{bit_depth}.jpg")
                        os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
        
                        # Save the image to the specified path.
                        output_path = os.path.join(OUTPUT_DIRECTORY, 
                                                   output_filename)
                        encoded_image.save(output_path)
                        
                # Otherwise, save the encoded image as JPEG.
                elif file[-4:] == "jpeg":
                    output_filename = (
                      f"{filename}_{colour_combination}_{bit_depth}.jpeg")
                    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
        
                    # Save the image to the specified path.
                    output_path = os.path.join(OUTPUT_DIRECTORY, 
                                               output_filename)
                    encoded_image.save(output_path)

    df = pd.DataFrame(results)
    
    # Save the results to an Excel file.
    df.to_excel(EXCEL_FILE, index=False)
    
if __name__ == "__main__":
    # Lorem Ipsum text file of substantial length so the full image is encoded.
    text_file_name = "Lorem_ipsum.txt"

    # Load each character of the text file.
    with open(text_file_name) as f:
        contents = f.read()

if ACTIVATE_BUTTON == False:
    # Display GUI.
    gui_compare = GuiCompareApp(0)
    gui_compare.ShowDialog()
    gui_compare.MainLoop()
    
else:
    # Transfer data of image quality measures of user-chosen images.
    excel_data_transfer()
