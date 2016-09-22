import xml.etree.ElementTree as ET
import optparse
import csv


def getTrackDict(root):
    ''' get the Track ID for every object '''
    track_ids_ = {}
    spotIDs = {}
    for frame in root[0][1]:
        for spot in frame:
            IDkey = int(spot.attrib.get('ID'))
            spotIDs[IDkey] = IDkey
    
    for track in root[0][2]:   
        for edge in track:
            IDkey = int(edge.attrib.get('SPOT_SOURCE_ID'))
            track_ids_[IDkey] = int(track.attrib.get('TRACK_ID'))
            spotIDs.pop(IDkey, None)

            IDkey = int(edge.attrib.get('SPOT_TARGET_ID'))
            track_ids_[IDkey] = int(track.attrib.get('TRACK_ID'))
            spotIDs.pop(IDkey, None)

    for IDkey in spotIDs.keys():
        track_ids_[IDkey] = 'None'

    return track_ids_


if __name__ == '__main__':

    parser = optparse.OptionParser(description='XML to CSV Converter')

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
        tablewriter.writerow(['trackID'] + root[0][1][0][0].keys())
 

        track_ids = getTrackDict(root)

        for frame in root[0][1]:
            for spot in frame:
                row = [track_ids[int(spot.attrib.get('ID'))]] + spot.attrib.values()
                tablewriter.writerow(row)


    featureTable.close()