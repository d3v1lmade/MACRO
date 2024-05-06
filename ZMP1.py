from astroquery.sdss import SDSS
from astropy.io import ascii
from astropy.table import Table

import csv
import io
import numpy as np
import requests

from photutils.aperture import CircularAperture, aperture_photometry
from photutils import datasets
import matplotlib.pyplot as plt

import sys



def perform_photometry(filename):
    image_data = datasets.load_star_image(filename)

    

    image_data = image_data.data

    

    x = 0
    y = 0

    # Performing the photometry
    positions = [(x,y)]  #Defining the position of the star
    apertures = CircularAperture(positions, r=4.)   #Defining the aperture size
    phot_table = aperture_photometry(image_data, apertures)  #Performing the photometry
    print(phot_table)  #Printing the photometry results
    return phot_table

def query_sdss(): 
    # Accessing SDSS Database
    url = "https://skyserver.sdss.org/dr17/en/tools/search/sql.aspx"
    query = "SELECT objID, ra, dec DROM PhotoObj WHERE ra BETWEEN min_ra AND max_ra AND dex BETWEEN min_dec AND max_dec"
    payload = {"cmd": query, "format": "csv"}
#    response = SDSS.query_sql(query)

    try:
        #defining additional headers if needed
        headers = {"User-Agent": "Your USer Agent String"}

        # Sending the request to SDSS server
        response = requests.get(url, params=payload, headers=headers)
        response.raise_for_status() #Raises an exception if the response is not 200
        #  data = ascii.read(io.BytesIO(response.content), format = 'csv', guess = False, fill_values=[('N/A', 0)], header_start=2, data_start=3)

        print(response.text)
        if "DOCTYPE html" in response.text:
            raise ValueError("Error: Received HTML response from SDSS")
        
        # Parsing the CSV data from the response
        csv_data = response.text

        
        #converting the data to an astropy.table.Table 
        table = ascii.read(io.StringIO(csv_data), format='csv')
        print(table.colnames)
        return table

    except requests.exceptions.RequestException as e:
        print(f"Error querying SDSS: {e}")
        return None
    
    except ValueError as e:
        print(f"Error reading data:{e}")
        return None
    
    max_cols = max([len(row) for row in data])
    for row in  data:
        if len(row) < max_cols:
            row.add_row([0])

    print(data)
    return  data

def main(filename):
    #Integrating Photometry and SDSS queries

    #Performing photometry on the file
    photometry_results  = perform_photometry(filename)

    #Query SDSS for additional data
    sdss_data = query_sdss()

    #Trying to match positions from photometry with SDSS results based on coordinates
    combined_data = []
    for source in photometry_results:
        for sdss_obj in sdss_data:
            if source['xcenter'] == sdss_obj['ra'] and source['ycenter'] == sdss_obj['dec']:
                print("Match found")
                combined_data = {'source_id': sdss_obj['objID'], 'flux': source['aperture_sum']}
                print("Here is the combined data: ", combined_data)
            else:
                print("No match found")

    
    # Analyzing the data 
    for data in combined_data:
        if data['flux'] > 0:
            print("The star is visible")
            print("The star's ID is: ", data['source_id'])
            print("The star's flux is: ", data['flux'])
        else:
            print("The star is not visible")

def is_2d_array(data):
    return len(np.array(data).shape) == 2

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: python ZMP.py <filename>')
        sys.exit(1)
    
    filename = sys.argv[1]

    image_data = main(filename)

    if not is_2d_array(image_data):
        print('Image data is not 2D')
        sys.exit(1)