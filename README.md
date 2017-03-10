# MaMuT Converter

A converter for visualising ilastik projects in the MaMuT plugin(Fiji/ImageJ). 

Usage:

0. Export the tracking results from ilastik as `H5 event Sequence` from the `Tracking` applet. This provides you with a folder full of numbered `*.h5` files.

1. Save the raw images as HDF/XML file

	1. open Fiji 
	2. import your raw image data 

				- use the hdf5 plugin, when your data is in HDF5 format (Help -- Update Fiji -- HDF5) 

	3. open BigDataViewer Plugin -> Export current Image as XML/HDF5

				- the freshly exported XML and HDF5 should be in the same folder
				- the name and path of the XML are input-parameters for the script in 2 (input-xml, xml-dir)

2. Execute the hdf_to_xml.py script

	```bash 
	python hdf_to_xml.py --parameters
	``` 

	parameters
	```
			--input-dir: path to the event sequence folder (as created in step 0)
			--input-raw: filepath to the HDF5 raw file (Yes, you need the raw data as HDF5 file AND the HDF5 file that was exported before, and the two are different)
			--raw-filepath: filepath in the HDF5 raw file
			--output-dir: full folderpath where the file should be saved
			--input-xml: filename of the input xml from 1 (without the path!)
			--xml-dir: folderpath that contains the input-xml (needs to be seperated, no filename)
			[--is-3D: 1 if the input is in 3D (default 0)]
			[--axes-order-raw: the axes order of the raw input (default txyzc)]
			[--axes-order-label: axes order of the label input (default xyzc, without t)]
	```

	Example:
	```bash 
	python hdf_to_xml.py --input-dir <PATH> --input-raw <PATH> --raw-filepath <PATH> --input-xml <XML-NAME> --xml-dir <PATH> 
	``` 
	A file called 'output.xml' will be saved to the <--output-dir Path>

3. Open the output.xml with the MaMuT-plugin (MaMuT -- load MaMuT File)

	1. When opening 2D Images in the MaMuT-Viewer: 
	```
		Dont forget to scroll in z until its on 0 (Hotkey-information by clicking 'help')
		Go to Settings and change the Brightness & Color 
	```
