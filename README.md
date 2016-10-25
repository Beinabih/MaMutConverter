# MaMut Converter

A converter for visualising ilastik projects in the MaMut plugin(Fiji/ImageJ). 

Usage:

	1. Save the raw images as HDF/XML file

		step 1: open Fiji
		step 2: import your raw image data
		step 3: open BigDataViewer Plugin -> Export current Image as XML/HDF5

	2. Execute the hdf_to_xml.py script

		parameters: --input-dir: path to the event sequence folder 
					--input-raw: filepath to the HDF5 raw file 
					--raw-filepath: filepath in the HDF5 raw file
					--output-dir: folder where the file should be saved
					--input-xml: name of the input xml from 1 
					--xml-dir: path to the input-xml (needs to be seperated)
					--is-3D: 1 if the input is in 3D (default 0)
					--axes-order-raw: the axes order of the raw input (default txyzc)
					--axes-order-label: axes order of the label input (default xyzc, without t)

	3. Open the output.xml with MaMut