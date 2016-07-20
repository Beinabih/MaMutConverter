import xml.etree.ElementTree as ET
import glob
import optparse
import numpy as np
import h5py
import csv


def getTrackDict(root):
    ''' get the Track ID for every object '''
    track_ids_ = {}
    for track in root[0][2]:
        for edge in track:
            track_ids_[int(edge.attrib.get('SPOT_TARGET_ID'))] = int(track.attrib.get('TRACK_ID'))

    for frame in root[0][1]:
        for spot in frame:
            if int(spot.attrib.get('ID')) not in track_ids_.keys():
                track_ids_[int(spot.attrib.get('ID'))] = 'None'

    return track_ids_


if __name__ == '__main__':

    parser = optparse.OptionParser(description='hdf to xml')

    parser.add_option('--input-xml', type=str, dest='input_xml',
                      help='Filename for the xml file')
    parser.add_option('--output-dir', type=str, dest='output_dir', default=".",
                      help='Filepath for the csv table file')

    # parse command line
    opt, args = parser.parse_args()

    tree = ET.parse(opt.input_xml)
    root = tree.getroot()

    with open(opt.output_dir + '/mamut_table.csv', 'w') as featureTable:
        tablewriter = csv.writer(featureTable, delimiter=',')
        #tablewriter.writerow(['trackID', 'time', 'objID', 'xpos', 'ypos', 'Radius', 'Brightness'])
        tablewriter.writerow(['trackID'] + root[0][1][1][1].keys())

        track_ids = getTrackDict(root)

        for frame in root[0][1]:
            for spot in frame:
                print [track_ids[int(spot.attrib.get('ID'))]] + spot.attrib.values()
                row = [track_ids[int(spot.attrib.get('ID'))]] + spot.attrib.values()
                tablewriter.writerow(row)


    featureTable.close()