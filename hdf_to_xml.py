import numpy as np
import h5py
import vigra
import xml.etree.ElementTree as ET




def getCentroids(label):
		centroid_feat = vigra.analysis.extractRegionFeatures(np.float32(labels), np.uint32(labels), features='RegionCenter')
		regionCentroids = centroid_feat['RegionCenter']
		return regionCentroids



if __name__ == '__main__':

	len_files = 4

	tree = ET.parse('/Users/jmassa/Documents/MaMut_project/xml_ex/raw_input.xml')
	root = tree.getroot()
	allspots = ET.SubElement(root[0], 'AllSpots')
	cell_id = 0

	for t in xrange(len_files):
		rawimage_filename = '/Users/jmassa/Documents/MaMut_project/mamut_bridge/events/old/0000{}.h5'.format(t)
		spotsInFrame = ET.SubElement(allspots, 'SpotsInFrame')
		spotsInFrame.set('frame', str(t))

		with h5py.File(rawimage_filename, 'r') as h5raw:
			labels = h5raw['/segmentation/labels'].value

			regionCentroid = getCentroids(labels)

			for child in root:
				print child.tag, child.attrib

			root[0]

			for i in xrange(len(np.unique(labels))-1):
				xpos = regionCentroid[i+1,0]
				ypos = regionCentroid[i+1,1]
				tpos = t
				print xpos, ypos
				spot = ET.SubElement(spotsInFrame, 'Spot ID="{}" name="center" VISIBILITY="1" POSITION_T="{}" POSITION_Z="0" POSITION_Y="{}" RADIUS="4.028827888855088" FRAME="0" POSITION_X="{}" QUALITY="3.0" '.format(str(cell_id),str(tpos),str(ypos),str(xpos)))
				cell_id +=1

	ET.dump(allspots)
	
	for allspots in root.iter('AllSpots'):
		#allspots.text = 'motherrucker'
		allspots.set('nspots', str(cell_id))

	alltracks = ET.SubElement(root[0], 'AllTracks')
	filteredTracks = ET.SubElement(root[0], 'FilteredTracks')
	track = ET.SubElement(alltracks, 'Track')
	trackid = ET.SubElement(filteredTracks, 'TrackID')


	ET.dump(alltracks)


	tree.write('output.xml')



