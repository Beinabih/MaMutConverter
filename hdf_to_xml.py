import numpy as np
import h5py
import vigra
import xml.etree.ElementTree as ET
import glob
#import lxml.etree as etree

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

def getCentroids(label):
		centroid_feat = vigra.analysis.extractRegionFeatures(np.float32(labels), np.uint32(labels), features='RegionCenter')
		regionCentroids = centroid_feat['RegionCenter']
		return regionCentroids

def getUniqueIds(timesteps):
	unique_ids = {}
	uid = 0

	for t in timesteps:
		labelimage_filename = '/Users/jmassa/Documents/MaMut_project/mamut_bridge/events/0000{}.h5'.format(t)
		with h5py.File(labelimage_filename, 'r') as h5raw:
			labelimage = h5raw['/segmentation/labels'].value
			unique_ids[t] = {}
			for ids in np.unique(labelimage):
				unique_ids[t][ids] = uid
				uid += 1
	return unique_ids

if __name__ == '__main__':


	images = sorted(glob.glob("/Users/jmassa/Documents/MaMut_project/mamut_bridge/events/*.h5"))

	tree = ET.parse('/Users/jmassa/Documents/MaMut_project/xml_ex/raw_input.xml')
	root = tree.getroot()
	allspots = ET.SubElement(root[0], 'AllSpots')
	alltracks = ET.SubElement(root[0], 'AllTracks')
	filteredTracks = ET.SubElement(root[0], 'FilteredTracks')
	cell_count = 0
	track_id = 0
	track_ref_dic = {}
	ids = getUniqueIds(range(len(images)))

	for t,file_path in enumerate(images):
		rawimage_filename = file_path
		spotsInFrame = ET.SubElement(allspots, 'SpotsInFrame')
		spotsInFrame.set('frame', str(t))

		with h5py.File(rawimage_filename, 'r') as h5raw:
			labels = h5raw['/segmentation/labels'].value

			#in skimage + radius
			regionCentroid = getCentroids(labels)
			cell_count += regionCentroid.shape[0]-1

			for child in root:
				print child.tag, child.attrib

			for i in np.unique(labels):
				if i != 0 :
					xpos = regionCentroid[i,0]
					ypos = regionCentroid[i,1]
					tpos = t
					print xpos, ypos
					spot = ET.SubElement(spotsInFrame, 'Spot ID="{}" name="center" VISIBILITY="1" POSITION_T="{}" POSITION_Z="0" POSITION_Y="{}" RADIUS="4.028827888855088" FRAME="{}" POSITION_X="{}" QUALITY="3.0" '.format(str(ids[t][i]),str(float(tpos)),str(ypos),str(t),str(xpos)))
				
			try:
				move_table = h5raw['/tracking/Moves'].value
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


	tree.write('output.xml')




