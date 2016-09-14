import vigra
import xml.etree.ElementTree as ET
import glob
import optparse
import numpy as np
import h5py
from skimage.external import tifffile


def indent(elem, level=0):
    '''line indentation in the xml file '''
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

def convertKeyName(key):
    key = key.replace('<', '_')
    key = key.replace('>', '')
    key = key.replace(' ', '')
    return key


def getFeatures(rawimage, labelimage, is_3D):
    '''get centroids and radius of a cell'''
    if is_3D == 0 and labelimage.ndim == 3:
        labelimage = np.squeeze(labelimage)
    rawimage = np.squeeze(rawimage)
    # print "getFeatures", rawimage.shape, labelimage.shape
    features = vigra.analysis.extractRegionFeatures(np.float32(rawimage), np.uint32(labelimage))
    regionCentroids = features['RegionCenter']
    regionradii = features['RegionRadii']
    #regionSum = features['Sum']
    return regionCentroids, regionradii, features

def getUniqueIds(image_list):
    ''' unique ids for the cells'''
    unique_ids = {}
    uid = 0

    for timestep, path in enumerate(image_list):
        labelimage_filename = path
        with h5py.File(labelimage_filename, 'r') as h5raw:
            labelimage = h5raw['/segmentation/labels'].value
            unique_ids[timestep] = {}
            for label in np.unique(labelimage):
                unique_ids[timestep][label] = uid
                uid += 1
    return unique_ids

def getShortname(string):
    ''' convert name to shortname'''
    shortname = string[0:2]
    for i, l in enumerate(string):
        try:
            if l == "_":
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

def setFeatures(rawimage, labelimage_filename, is_3D, axes_order_label):
    ''' set features in the xml '''
    with h5py.File(labelimage_filename, 'r') as h5raw:
        labelimage = h5raw['/segmentation/labels'].value
        labelimage = checkAxes(labelimage, is_3D, axes_order_label, False)
        #if changed
        #labelimage = np.swapaxes(labelimage, 0, 1)

        rawimage = np.squeeze(rawimage)
        # print 'setFeatures', rawimage.shape, labelimage.shape

        if is_3D == 0 and labelimage.ndim == 3:
            labelimage = np.squeeze(labelimage)

        features = vigra.analysis.extractRegionFeatures(np.float32(rawimage), np.uint32(labelimage))

        for key in features:
            feature_string = key
            feature_string = convertKeyName(feature_string)
            if len(feature_string) > 15:
                shortname = getShortname(feature_string).replace('_', '')
            else:
                shortname = feature_string.replace('_', '')

            if (np.array(features[key])).ndim == 2:
                if key != 'Histogram':
                    #print key, np.array(features[key]).shape
                    for column in xrange((np.array(features[key])).shape[1]):
                        newfeature = ET.SubElement(root[0][0][0], 'Feature dimension="NONE" feature="{}" name="{}" shortname="{}"'.format(feature_string + '_' + str(column),
                                                                                                                                          feature_string, shortname + '_' + str(column)))

            else:
                #print "ELSE", key, np.array(features[key]).shape
                newfeature = ET.SubElement(root[0][0][0], 'Feature dimension="NONE" feature="{}" name="{}" shortname="{}"'.format(feature_string,
                                                                                                                                  feature_string, shortname))

            if isinstance(features[key], int):
                newfeature.set('isint', 'true')
            else:
                newfeature.set('isint', 'false')

def changeAxesOrder(volume, input_axes, output_axes='txyzc'):
    outVolume = volume

    # find present and missing axes
    positions = {}
    missingAxes = []
    for axis in output_axes:
        try:
            positions[axis] = input_axes.index(axis)
        except ValueError:
            missingAxes.append(axis)

    # insert missing axes at the end
    for m in missingAxes:
        outVolume = np.expand_dims(outVolume, axis=-1)
        positions[m] = outVolume.ndim - 1

    # transpose
    axesRemapping = [positions[a] for a in output_axes]
    outVolume = np.transpose(outVolume, axes=axesRemapping)

    return outVolume

def checkAxes(volume, is_3D, axes_order, raw):

    if raw:
        if is_3D == 1:
            if axes_order != "txyzc":
                volume = changeAxesOrder(volume, axes_order, output_axes='txyzc')
        else:
            if axes_order != "txyc":
                volume = changeAxesOrder(volume, axes_order, output_axes='txyc')
    else:
        if is_3D == 1:
            if axes_order != "xyzc":
                volume = changeAxesOrder(volume, axes_order, output_axes='xyzc')
        else:
            if axes_order != "xyc":
                volume = changeAxesOrder(volume, axes_order, output_axes='xyc')

    return volume


if __name__ == '__main__':

    parser = optparse.OptionParser(description='hdf to xml')

    # file paths
    parser.add_option('--input-dir', type=str, dest='input_dir', default=".",
                      help='Folder where the h5 event sequences are created')
    parser.add_option('--input-raw', type=str, dest='input_raw', default=".",
                      help='the raw input image')
    # parser.add_option('--raw-filepath', type=str, dest='raw_filepath', default="data",
    #                   help='hdf5 Filepath of the raw_input')
    parser.add_option('--input-xml', type=str, dest='input_xml',
                      help='Filename for the xml image file')
    parser.add_option('--xml-dir', type=str, dest='xml_dir',
                      help='Filepath for the xml image file')
    parser.add_option('--output-dir', type=str, dest='output_dir', default=".",
                      help='Filepath for the xml image file')
    parser.add_option('--is-3D', type=int, dest='is_3D', default=0,
                      help='if file is 3D')
    parser.add_option('--axes-order-raw', type=str, dest='axes_order_raw', default="txyzc",
                      help='the axes order of the raw file')
    parser.add_option('--axes-order-label', type=str, dest='axes_order_label', default="xyzc",
                      help='the axes order of the labelfile')

    # parse command line
    opt, args = parser.parse_args()

    images = sorted(glob.glob(opt.input_dir + "/*.h5"))

    tree = ET.parse('raw_input.xml')
    root = tree.getroot()
    allspots = ET.SubElement(root[0], 'AllSpots')
    alltracks = ET.SubElement(root[0], 'AllTracks')
    filteredTracks = ET.SubElement(root[0], 'FilteredTracks')
    cell_count = 0
    track_id = 0
    track_ref_dic = {}
    ids = getUniqueIds(images)
    #raw_images = np.float32(tifffile.imread(opt.input_raw))

    with h5py.File(opt.input_raw, 'r') as h5raw:
        print "group name --->", str(h5raw.items()[0][0])
        raw_images = np.array(h5raw.get(str(h5raw.items()[0][0]))) # assumes the data is in the top level  group 

    # with h5py.File(opt.input_raw, 'r') as h5raw:
    #     raw_images = np.float32(h5raw[opt.raw_filepath].value)
    # print raw_images.shape

    raw_images = checkAxes(raw_images, opt.is_3D, opt.axes_order_raw, True)
    # for tcxy order
    # if raw_images.ndim == 4:
    #     raw_images = np.rollaxis(raw_images, 1, 4)

    setFeatures(raw_images[0], images[1], opt.is_3D, opt.axes_order_label)

    for t, file_path in enumerate(images):
        rawimage_filename = file_path
        spotsInFrame = ET.SubElement(allspots, 'SpotsInFrame')
        spotsInFrame.set('frame', str(t))

        with h5py.File(rawimage_filename, 'r') as h5raw:

            labels = h5raw['/segmentation/labels'].value
            labels = checkAxes(labels, opt.is_3D, opt.axes_order_label, False)
            # labels = np.swapaxes(labels, 0, 1)
            # print raw_images.shape, labels.shape

            regionCentroid, regionRadii, features = getFeatures(raw_images[t], labels, opt.is_3D)
            cell_count += regionCentroid.shape[0]-1

            for i in np.unique(labels):
                if i != 0:
                    xpos = regionCentroid[i, 0]
                    ypos = regionCentroid[i, 1]

                    if opt.is_3D == 1:
                        zpos = regionCentroid[i, 2]
                    else:
                        zpos = 0.0

                    tpos = t
                    radius = 2*regionRadii[i, 0]
                    #cellSum = np.mean(regionSum[i])
                    spot = ET.SubElement(spotsInFrame, '''Spot ID="{}" name="center" VISIBILITY="1" POSITION_T="{}"
                                POSITION_Z="{}" POSITION_Y="{}" RADIUS="{}" FRAME="{}" 
                                POSITION_X="{}" QUALITY="3.0"'''.format(str(ids[t][i]), str(float(tpos)), str(zpos), str(ypos), str(radius),
                                                                        str(t), str(xpos)))

                    # for keys in features:
                    #     if keys != 'Histogram':
                    #         # print np.array(features[keys]).ndim
                    #         # print features[keys]
                    #         if (np.array(features[keys])).ndim == 0:
                    #             spot.set(convertKeyName(keys), str(np.nan_to_num(features[keys])))
                    #         if (np.array(features[keys])).ndim == 1:
                    #             spot.set(convertKeyName(keys), str(np.nan_to_num(features[keys][i])))
                    #         if (np.array(features[keys])).ndim == 2:
                    #             for j in xrange((np.array(features[keys])).shape[1]):
                    #                 spot.set(convertKeyName(keys) + '_{}'.format(str(j)), str(np.nan_to_num(features[keys][i, j])))
                    #                 #spot.set(convertKeyName(keys) + '_y', str(np.nan_to_num(features[keys][i, 1])))


            # write splits in file
            try:
                split_table = h5raw['/tracking/Splits'].value
                for s in split_table:
                    if (t-1, s[0]) in track_ref_dic:
                        edge_one = ET.SubElement(track_ref_dic[t-1, s[0]], '''Edge SPOT_SOURCE_ID="{}" SPOT_TARGET_ID="{}"
                                LINK_COST="-1.0" VELOCITY="0.0" DISPLACEMENT="0.0"'''.format(str(ids[t-1][s[0]]), str(ids[t][s[1]])))
                        edge_two = ET.SubElement(track_ref_dic[t-1, s[0]], '''Edge SPOT_SOURCE_ID="{}" SPOT_TARGET_ID="{}"
                                LINK_COST="-1.0" VELOCITY="0.0" DISPLACEMENT="0.0"'''.format(str(ids[t-1][s[0]]), str(ids[t][s[2]])))
                        track_ref_dic[t, s[1]] = track_ref_dic[t-1, s[0]]
                        track_ref_dic[t, s[2]] = track_ref_dic[t-1, s[0]]
                    else:
                        track_ref_dic[t, s[1]] = ET.SubElement(alltracks, 'Track')
                        track_ref_dic[t, s[1]].set('TRACK_ID', str(track_id))
                        track_ref_dic[t, s[1]].set("name", 'Track_{}'.format(str(track_id)))
                        track_ref_dic[t, s[1]].set("TRACK_INDEX", str(track_id))
                        trackid = ET.SubElement(filteredTracks, 'TrackID TRACK_ID="{}"'.format(str(track_id)))
                        track_id += 1
                        edge_one = ET.SubElement(track_ref_dic[t, s[1]], '''Edge SPOT_SOURCE_ID="{}" SPOT_TARGET_ID="{}"
                                LINK_COST="-1.0" VELOCITY="0.0" DISPLACEMENT="0.0"'''.format(str(ids[t-1][s[0]]), str(ids[t][s[1]])))
                        edge_two = ET.SubElement(track_ref_dic[t, s[2]], '''Edge SPOT_SOURCE_ID="{}" SPOT_TARGET_ID="{}"
                                LINK_COST="-1.0" VELOCITY="0.0" DISPLACEMENT="0.0"'''.format(str(ids[t-1][s[0]]), str(ids[t][s[2]])))
                    has_table = True
            except KeyError:
                print "no split in the sequence"
                has_table = False
            # write tracking in file
            try:
                move_table = h5raw['/tracking/Moves'].value
                for m in move_table:
                    if has_table:
                        if (t-1, m[0]) not in split_table:

                            if (t-1, m[0]) in track_ref_dic:
                                edge = ET.SubElement(track_ref_dic[t-1, m[0]], '''Edge SPOT_SOURCE_ID="{}" SPOT_TARGET_ID="{}"
                                        LINK_COST="0.0" VELOCITY="0.0" DISPLACEMENT="0.0"'''.format(str(ids[t-1][m[0]]), str(ids[t][m[1]])))
                                track_ref_dic[t, m[1]] = track_ref_dic[t-1, m[0]]
                            else:
                                #new track
                                track_ref_dic[t, m[1]] = ET.SubElement(alltracks, 'Track')
                                track_ref_dic[t, m[1]].set('TRACK_ID', str(track_id))
                                track_ref_dic[t, m[1]].set("name", 'Track_{}'.format(str(track_id)))
                                track_ref_dic[t, m[1]].set("TRACK_INDEX", str(track_id))
                                trackid = ET.SubElement(filteredTracks, 'TrackID TRACK_ID="{}"'.format(str(track_id)))
                                track_id += 1
                                edge = ET.SubElement(track_ref_dic[t, m[1]], '''Edge SPOT_SOURCE_ID="{}" SPOT_TARGET_ID="{}"
                                        LINK_COST="0.0" VELOCITY="0.0" DISPLACEMENT="0.0"'''.format(str(ids[t-1][m[0]]), str(ids[t][m[1]])))

                    else:

                        if (t-1, m[0]) in track_ref_dic:
                            edge = ET.SubElement(track_ref_dic[t-1, m[0]], '''Edge SPOT_SOURCE_ID="{}" SPOT_TARGET_ID="{}"
                                    LINK_COST="0.0" VELOCITY="0.0" DISPLACEMENT="0.0"'''.format(str(ids[t-1][m[0]]), str(ids[t][m[1]])))
                            track_ref_dic[t, m[1]] = track_ref_dic[t-1, m[0]]
                        else:
                            #new track
                            track_ref_dic[t, m[1]] = ET.SubElement(alltracks, 'Track')
                            track_ref_dic[t, m[1]].set('TRACK_ID', str(track_id))
                            track_ref_dic[t, m[1]].set("name", 'Track_{}'.format(str(track_id)))
                            track_ref_dic[t, m[1]].set("TRACK_INDEX", str(track_id))
                            trackid = ET.SubElement(filteredTracks, 'TrackID TRACK_ID="{}"'.format(str(track_id)))
                            track_id += 1
                            edge = ET.SubElement(track_ref_dic[t, m[1]], '''Edge SPOT_SOURCE_ID="{}" SPOT_TARGET_ID="{}"
                                    LINK_COST="0.0" VELOCITY="0.0" DISPLACEMENT="0.0"'''.format(str(ids[t-1][m[0]]), str(ids[t][m[1]])))
            except KeyError:
                print "no tracking in the event sequence"



    ET.dump(allspots)

    for allspots in root.iter('AllSpots'):
        allspots.set('nspots', str(cell_count))

    ET.dump(alltracks)
    indent(root)

    #'height= 'instead of 'height =' gives a wrong picture position
    image_data = ET.SubElement(root[1], '''ImageData filename="{}" folder="{}" height ="0" nframes="0" nslices="0"
                    pixelheight="1.0" pixelwidth="1.0" timeinterval="1.0" voxeldepth="1.0" width="0" '''.format(opt.input_xml, opt.xml_dir))
    ET.dump(image_data)


    tree.write(opt.output_dir + '/output.xml')




