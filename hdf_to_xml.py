import vigra
import xml.etree.ElementTree as ET
import glob
import optparse
import numpy as np
import h5py
from skimage.external import tifffile
from mamutexport import mamutxmlbuilder

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

def convertKeyName(key):
    key = key.replace('<', '_')
    key = key.replace('>', '')
    key = key.replace(' ', '')
    return key

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

def setFeatures(builder, rawimage, labelimage_filename, is_3D, axes_order_label):
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

            isInt = isinstance(features[key], int)

            if (np.array(features[key])).ndim == 2:
                if key != 'Histogram':
                    #print key, np.array(features[key]).shape
                    for column in xrange((np.array(features[key])).shape[1]):
                        builder.addFeatureName(feature_string + '_' + str(column), feature_string, shortname + '_' + str(column), isInt)

            else:
                #print "ELSE", key, np.array(features[key]).shape
                builder.addFeatureName(feature_string, feature_string, shortname, isInt)
                
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
        elif axes_order == "txyzc":
                volume = changeAxesOrder(np.expand_dims(volume.squeeze(), axis=-1), 'xyc', output_axes='xyc')
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
    parser.add_option('--raw-filepath', type=str, dest='raw_filepath', default="data",
                      help='hdf5 Filepath of the raw_input')
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
    builder = mamutxmlbuilder.MamutXmlBuilder()
    
    cell_count = 0
    next_track_id = 0
    track_ref_dic = {}
    ids = getUniqueIds(images)
    # raw_images = np.float32(tifffile.imread(opt.input_raw))

    # with h5py.File(opt.input_raw, 'r') as h5raw:
    #     print "group name --->", str(h5raw.items()[0][0])
    #     raw_images = np.array(h5raw.get(str(h5raw.items()[0][0]))) # assumes the data is in the top level  group 

    with h5py.File(opt.input_raw, 'r') as h5raw:
        raw_images = np.float32(h5raw[opt.raw_filepath].value)
    print raw_images.shape

    raw_images = checkAxes(raw_images, opt.is_3D, opt.axes_order_raw, True)
    # for tcxy order
    # if raw_images.ndim == 4:
    #     raw_images = np.rollaxis(raw_images, 1, 4)

    setFeatures(builder, raw_images[0], images[1], opt.is_3D, opt.axes_order_label)
    builder.addFeatureName("LabelimageId", "LabelimageId", "labelid", False)
    builder.addFeatureName("Track_color", "Track_color", "trackcol", False)
    builder.addTrackFeatureName("Track_color", "Track_color", "trackcol", False)

    for t, file_path in enumerate(images):
        print "timestep: ", t
        rawimage_filename = file_path

        with h5py.File(rawimage_filename, 'r') as h5raw:
            # write splits in file
            try:
                split_table = h5raw['/tracking/Splits'].value
                for s in split_table:
                    print 'split_table', s
                    if (t-1, s[0]) in track_ref_dic:
                        track_id = track_ref_dic[t-1, s[0]]
                    else:
                        track_id = next_track_id
                        next_track_id += 1
                        track_ref_dic[t-1, s[0]] = track_id
                    builder.addSplit(track_id, ids[t-1][s[0]], [ids[t][s[1]], ids[t][s[2]]])
                    track_ref_dic[t, s[1]] = track_id
                    track_ref_dic[t, s[2]] = track_id
                    has_table = True
            except KeyError:
                print "no split in the sequence"
                has_table = False

            # write tracking in file
            try:
                move_table = h5raw['/tracking/Moves'].value
                for m in move_table:
                    if not (has_table and m[0] in split_table[:, 0]):
                        if (t-1, m[0]) in track_ref_dic:
                            track_id = track_ref_dic[t-1, m[0]]
                        else:
                            track_id = next_track_id
                            next_track_id += 1
                            track_ref_dic[t-1, m[0]] = track_id
                        builder.addLink(track_id, ids[t-1][m[0]], ids[t][m[1]])
                        track_ref_dic[t, m[1]] = track_id
            except KeyError:
                print "no tracking in the event sequence"

    randomColorPerTrack = {}
    for trackId in range(next_track_id):
        randomColorPerTrack[trackId] = np.random.random()
        builder.setTrackFeatures(trackId, {'Track_color': randomColorPerTrack[trackId]})

    # Need second for-loop so that we know the trackId for objects in the first frame 
    for t, file_path in enumerate(images):
        print "timestep: ", t
        rawimage_filename = file_path

        with h5py.File(rawimage_filename, 'r') as h5raw:
            labels = h5raw['/segmentation/labels'].value
            labels = checkAxes(labels, opt.is_3D, opt.axes_order_label, False)
            # labels = np.swapaxes(labels, 0, 1)
            # print raw_images.shape, labels.shape

            regionCentroid, regionRadii, features = getFeatures(raw_images[t], labels, opt.is_3D)
            cell_count += regionCentroid.shape[0]-1

            # add spots, including the trackId as name and a per-track random color
            for i in np.unique(labels):
                if i != 0:
                    xpos = regionCentroid[i, 0]
                    ypos = regionCentroid[i, 1]

                    if opt.is_3D == 1:
                        zpos = regionCentroid[i, 2]
                    else:
                        zpos = 0.0

                    radius = 2*regionRadii[i, 0]
                    #cellSum = np.mean(regionSum[i])

                    featureDict = {}
                    for keys in features:
                        if keys != 'Histogram':
                            # print np.array(features[keys]).ndim
                            # print features[keys]
                            if (np.array(features[keys])).ndim == 0:
                                featureDict[convertKeyName(keys)] = features[keys]
                            if (np.array(features[keys])).ndim == 1:
                                featureDict[convertKeyName(keys)] = features[keys][i]
                            if (np.array(features[keys])).ndim == 2:
                                for j in xrange((np.array(features[keys])).shape[1]):
                                    featureDict[convertKeyName(keys) + '_{}'.format(str(j))] = features[keys][i, j]

                    try:
                        trackId = track_ref_dic[t, i]
                    except KeyError:
                        trackId = next_track_id
                        next_track_id += 1
                        randomColorPerTrack[trackId] = np.random.random()
                        
                    featureDict['Track_color'] = randomColorPerTrack[trackId]
                    featureDict['LabelimageId'] = i
                    builder.addSpot(t, 'track-{}'.format(trackId), ids[t][i], xpos, ypos, zpos, radius, featureDict)

    #'height= 'instead of 'height =' gives a wrong picture position
    builder.setBigDataViewerImagePath(opt.xml_dir, opt.input_xml)
    builder.writeToFile(opt.output_dir + '/output.xml')

