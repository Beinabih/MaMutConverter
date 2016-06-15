import numpy as np
import h5py
import vigra
import xml.etree.ElementTree as ET
import glob
import optparse
import configargparse as argparse

def indent(elem, level=0):
    i = "\n" + level*"  "
    j = "\n" + (level-1)*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = j
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = j
    return elem    

def getCentroids(labelimage):
	centroid_feat = vigra.analysis.extractRegionFeatures(np.float32(labelimage), np.uint32(labelimage))
	regionCentroids = centroid_feat['RegionCenter']
	regionradii = centroid_feat['RegionRadii']
	return regionCentroids, regionradii

def getUniqueIds(images):
	unique_ids = {}
	uid = 0

	for t,file_path in enumerate(images):
		labelimage_filename = file_path
		with h5py.File(labelimage_filename, 'r') as h5raw:
			labelimage = h5raw['/segmentation/labels'].value
			unique_ids[t] = {}
			for ids in np.unique(labelimage):
				print t , ids
				unique_ids[t][ids] = uid
				uid += 1
	return unique_ids

def getShortname(string):
	shortname = string[0:2]
	for i,l in enumerate(string):
		try:
			if l == "_" :
				shortname += string[i+1]
				shortname += string[i+2]
				shortname += string[i+3]
			if shortname == 'WeReg':
				shortname += string[i+7]
				shortname += string[i+8]
				shortname += string[i+9]

		except IndexError:
			break
	return shortname.strip()

def setFeatures(labelimage_filename):

	with h5py.File(labelimage_filename, 'r') as h5raw:
		labelimage = h5raw['/segmentation/labels'].value
		features = vigra.analysis.extractRegionFeatures(np.float32(labelimage), np.uint32(labelimage))

		for key in features:
			feature_string = key
			feature_string = feature_string.replace('<', '_')
			feature_string = feature_string.replace('>','')
			feature_string = feature_string.replace(' ','')
			if len(feature_string) > 15 :
				shortname =  getShortname(feature_string).replace('_','')
			else:
				shortname = feature_string.replace('_','')
			newfeature = ET.SubElement(root[0][0][0], 'Feature feature="{}" name ="{}"'.format(feature_string, feature_string)) # shortname add


if __name__ == '__main__':

	parser = optparse.OptionParser(description='Compute TRA loss of a new labeling compared to ground truth')

    # file paths
	parser.add_option('--input-dir', type=str, dest='input_dir', default=".", 
		help='Folder where the h5 event sequences are created')
	parser.add_option('--input-xml', type=str, dest='input_xml', 
		help='Filename for the xml image file')
	parser.add_option('--xml-dir', type=str, dest='xml_dir', 
		help='Filepath for the xml image file')

	# parse command line
	opt , args = parser.parse_args()


	images = sorted(glob.glob(opt.input_dir +"/*.h5"))

	tree = ET.parse('raw_input.xml')
	root = tree.getroot()
	allspots = ET.SubElement(root[0], 'AllSpots')
	alltracks = ET.SubElement(root[0], 'AllTracks')
	filteredTracks = ET.SubElement(root[0], 'FilteredTracks')
	cell_count = 0
	track_id = 0
	track_ref_dic = {}
	ids = getUniqueIds(images)
	setFeatures(images[1])

	for t,file_path in enumerate(images):
		rawimage_filename = file_path
		spotsInFrame = ET.SubElement(allspots, 'SpotsInFrame')
		spotsInFrame.set('frame', str(t))

		with h5py.File(rawimage_filename, 'r') as h5raw:
			labels = h5raw['/segmentation/labels'].value

			regionCentroid, regionRadii = getCentroids(labels)
			cell_count += regionCentroid.shape[0]-1


			for i in np.unique(labels):
				if i != 0 :
					xpos = regionCentroid[i,0]
					ypos = regionCentroid[i,1]
					tpos = t
					radius = np.mean(regionRadii[i])
					spot = ET.SubElement(spotsInFrame, 'Spot ID="{}" name="center" VISIBILITY="1" POSITION_T="{}" POSITION_Z="0" POSITION_Y="{}" RADIUS="{}" FRAME="{}" POSITION_X="{}" QUALITY="3.0" '.format(str(ids[t][i]),str(float(tpos)),str(ypos),str(radius),str(t),str(xpos)))
				
			try:
				move_table = h5raw['/tracking/Moves'].value
				assert np.unique(move_table) == np.unique(labels), 'labels do not match'
				for m in move_table:
					if (t-1, m[0]) in track_ref_dic:
						edge = ET.SubElement(track_ref_dic[t-1, m[0]], 'Edge SPOT_SOURCE_ID="{}" SPOT_TARGET_ID="{}" LINK_COST="0.0" VELOCITY="0.0" DISPLACEMENT="0.0"'.format(str(ids[t-1][m[0]]),str(ids[t][m[1]])))
						track_ref_dic[t, m[1]] = track_ref_dic[t-1, m[0]]
					else:
						track_ref_dic[t, m[1]] = ET.SubElement(alltracks, 'Track')
						track_ref_dic[t, m[1]].set('TRACK_ID', str(track_id))
						track_ref_dic[t, m[1]].set("name", 'Track_{}'.format(str(track_id)))
						track_ref_dic[t, m[1]].set("TRACK_INDEX", str(track_id))
						trackid = ET.SubElement(filteredTracks, 'TrackID TRACK_ID="{}"'.format(str(track_id)))
						track_id += 1
						edge = ET.SubElement(track_ref_dic[t, m[1]], 'Edge SPOT_SOURCE_ID="{}" SPOT_TARGET_ID="{}" LINK_COST="0.0" VELOCITY="0.0" DISPLACEMENT="0.0"'.format(str(ids[t-1][m[0]]),str(ids[t][m[1]])))
			except KeyError:
				print "no tracking in the event sequence"

	ET.dump(allspots)

	for allspots in root.iter('AllSpots'):
		allspots.set('nspots', str(cell_count))

	ET.dump(alltracks)
	indent(root)

	image_data = ET.SubElement(root[1], 'ImageData filename="{}" folder="{}" height ="0" nframes="0" nslices="0" pixelheight="1.0" pixelwidth="1.0" timeinterval="1.0" voxeldepth="1.0" width="0" '.format(opt.input_xml, opt.xml_dir))
	ET.dump(image_data)


	tree.write('output.xml')




