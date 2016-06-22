import xml.etree.ElementTree as ET
import glob
import optparse
import numpy as np
import h5py
import csv


def getTrackDict(root):
    track_ids_ = {}
    for track in root[0][2]:
        print track.attrib
        for edge in track:
            print edge.attrib.values()[3]
            track_ids_[int(edge.attrib.values()[3])] = track.attrib.values()[1]

    for frame in root[0][1]:
        for spot in frame:
            if int(spot.attrib.values()[3]) not in track_ids_.keys():
                track_ids_[int(spot.attrib.values()[3])] = 'None'

    return track_ids_


if __name__ == '__main__':

    tree = ET.parse('output.xml')
    root = tree.getroot()

    print root[0][2].tag, int(root[0][1].attrib.values()[0])



    with open('blank.cvs', 'w') as featureTable:
        tablewriter = csv.writer(featureTable)
        tablewriter.writerow(['trackID', 'time', 'objID', 'xpos', 'ypos', 'Radius', 'Brightness'])

        track_ids = getTrackDict(root)

        for frame in root[0][1]:
            # print frame.tag
            for spot in frame:
                # print spot.attrib
                print spot.attrib.values()[3]
                tablewriter.writerow([track_ids[int(spot.attrib.values()[3])], spot.attrib.values()[8], spot.attrib.values()[3],
                                      spot.attrib.values()[5], spot.attrib.values()[6], spot.attrib.values()[7],
                                      spot.attrib.values()[1]])


    featureTable.close()