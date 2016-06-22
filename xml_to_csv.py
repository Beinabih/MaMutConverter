import xml.etree.ElementTree as ET
import glob
import optparse
import numpy as np
import h5py
import csv

if __name__ == '__main__':

    tree = ET.parse('output.xml')
    root = tree.getroot()

    print root[0][1][1].tag, int(root[0][1].attrib.values()[0])


    with open('blank.cvs', 'w') as featureTable:
        tablewriter = csv.writer(featureTable)
        tablewriter.writerow(['trackID', 'time', 'objID', 'xpos', 'ypos'])

        for i in root[0][1]:
            print i.tag




    featureTable.close()