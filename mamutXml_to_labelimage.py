import vigra
import xml.etree.ElementTree as ET
import glob
import optparse
import numpy as np
import h5py
import os

def getLabelImageForFrame(labelImageFilename, labelImagePath):
    """
    Get the label image(volume) of one time frame
    """
    with h5py.File(labelImageFilename, 'r') as h5file:
        return h5file[labelImagePath].value

def getShape(labelImageFilename, labelImagePath):
    """
    extract the shape from the labelimage
    """
    with h5py.File(labelImageFilename, 'r') as h5file:
        return h5file[labelImagePath].shape

def relabelImage(volume, replace):
    """
    Apply a set of label replacements to the given volume.
    Everything not present in "replace" will be set to zero

    Parameters:
        volume - numpy array
        replace - dictionary{[(oldValueInVolume)->(newValue), ...]}
    """
    mp = np.zeros(np.amax(volume) + 1, dtype=volume.dtype)
    
    for k, v in replace.iteritems():
        mp[k] = v

    return mp[volume]

if __name__ == '__main__':

    parser = optparse.OptionParser(description='Convert a Mamut XML (with possibly corrected tracks) back to a labelimage, as ilastik would export it')

    # file paths
    parser.add_option('--input-dir', type=str, dest='input_dir', default=".",
                      help='Folder where the h5 event sequences are created')
    parser.add_option('--mamut-xml', type=str, dest='input_xml',
                      help='Filename of the saved MaMuT xml image file')
    parser.add_option('--output', type=str, dest='output', help="Filename where the resulting labelimage will be saved")

    # parse command line
    opt, args = parser.parse_args()

    images = sorted(glob.glob(opt.input_dir + "/*.h5"))
    assert(len(images) > 0)
    labelImagePath = '/segmentation/labels'

    mamutXml = ET.parse(opt.input_xml)
    root = mamutXml.getroot()
    allSpots = root.find('Model').find('AllSpots')
    allTracks = root.find('Model').find('AllTracks')

    # find a mapping of spots to their labelimage ID and frame
    print("Mapping Spots back to labelimage IDs...")
    spotToLabelImageMapping = {}

    for spotsInFrame in allSpots.findall('SpotsInFrame'):
        currentFrame = int(spotsInFrame.attrib['frame'])

        for spot in spotsInFrame:
            labelId = int(float(spot.attrib['LabelimageId']))
            spotId = spot.attrib['ID']
            spotToLabelImageMapping[spotId] = (currentFrame, labelId)

    # follow all links
    print("Finding which spots belong to what tracks...")
    labelImageIdToTrackId = {}

    for track in allTracks:
        trackId = int(track.attrib['TRACK_ID']) + 2 # trackIds start at 2 in ilastik, but 0 in MaMuT

        # list source and target nodes of all edges as part of that track
        for edge in track:
            for v in ['SPOT_SOURCE_ID', 'SPOT_TARGET_ID']:
                spotLabelImageId = spotToLabelImageMapping[edge.attrib[v]]
                labelImageIdToTrackId.setdefault(spotLabelImageId[0], {})[spotLabelImageId[1]] = trackId

    # recolor label image
    print("Recoloring labelimage...")
    shape = getShape(images[0], labelImagePath)
    resultVolume = np.zeros((len(images),) + shape, dtype='uint16')

    for t, image in enumerate(images):
        labelImage = getLabelImageForFrame(image, labelImagePath)
        remapping = labelImageIdToTrackId[t]
        relabeledLabelImage = relabelImage(labelImage, remapping)
        resultVolume[t,...] = relabeledLabelImage

    # save
    if os.path.exists(opt.output):
        os.remove(opt.output)
    vigra.impex.writeHDF5(resultVolume, opt.output, 'exported_data', compression='gzip', chunks=True)

    print("Done")