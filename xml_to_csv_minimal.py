import xml.etree.ElementTree as ET
import optparse
import csv

attributeKeys = ['FRAME', 'name',\
                 'POSITION_X', 'POSITION_Y', 'RADIUS',\
                 'Coord_Minimum_0', 'Coord_Minimum_1',\
                 'Coord_Maximum_0', 'Coord_Maximum_1',\
                 'RegionRadii_0', 'RegionRadii_1',\
                 'Count']
                 
attributes = ['trackID'] + attributeKeys

nColRange = [87, 88, 89]

minAttributes = 5

def getTrackDict(root):
    """ get the Track ID for every object """
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

    for IDkey in spotIDs.keys():
        track_ids_[IDkey] = 'None'

    return track_ids_


if __name__ == '__main__':

    parser = optparse.OptionParser(description='XML to CSV converter')

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
        tablewriter.writerow(attributes)

        track_ids = getTrackDict(root)

        for frame in root[0][1]:
            for spot in frame:
                row = [track_ids[int(spot.attrib.get('ID'))]]
                nValues = len(spot.attrib.values())

                if (nValues in nColRange):
                    for key in attributeKeys:
                        row += [spot.attrib.get(key)]
                else:
                    for i in range(minAttributes):
                        row += [spot.attrib.get(attributeKeys[i])]

                tablewriter.writerow(row)

    featureTable.close()
