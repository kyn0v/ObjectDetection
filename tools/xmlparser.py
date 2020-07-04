# xml annotation parser and processing
import os
import sys
import glob
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from tqdm import tqdm
import numpy as np
import json
import shutil
import cv2
import imghdr


def changeFileNameInAnnotation(xmlFiles):
    for filePath in tqdm(xmlFiles):
        imgName = filePath.split("\\")[-1][:-4] + ".jpg"
        tree = ET.parse(filePath)
        root = tree.getroot()
        fileName = root.find('filename')
        fileName.text = imgName
        tree.write(filePath)

def showBBox(xmlFilePath):
    tree = ET.parse(xmlFilePath)
    root = tree.getroot()
    fileName = root.find('filename').text
    imagePath = xmlFilePath.replace("Annotations", "JPEGImages").replace(".xml", ".jpg")
    image = cv2.imread(imagePath)
    for objectInfo in root.findall('object'):
        bbox = objectInfo.find('bndbox')
        xmin = int(bbox.find('xmin').text)
        ymin = int(bbox.find('ymin').text)
        xmax = int(bbox.find('xmax').text)
        ymax = int(bbox.find('ymax').text)
        cv2.rectangle(image, (xmin, ymin), (xmax, ymax), (0,255,0), 2)
    cv2.imshow("bbox", image)
    cv2.waitKey(100000)

def analyzeObjectSize(xmlFiles):
    sizeCount = []
    for filePath in tqdm(xmlFiles):
        tree = ET.parse(filePath)
        root = tree.getroot()
        for objectInfo in root.findall('object'):
            bbox = objectInfo.find('bndbox')
            xmin = int(bbox.find('xmin').text)
            ymin = int(bbox.find('ymin').text)
            xmax = int(bbox.find('xmax').text)
            ymax = int(bbox.find('ymax').text)
            objectSize = (xmax - xmin) * (ymax - ymin)
            sizeCount.append(objectSize)
    bins = range(4000, 20000, 1000)
    counts, binEdge = np.histogram(sizeCount, bins)
    print(counts)
    plt.hist(sizeCount, bins)
    plt.show()


def selectObjectBySize(sizeRange, xmlFiles):
    for filePath in tqdm(xmlFiles):
        imageFileName = filePath.split("\\")[-1][:-4] + ".jpg"
        if not imghdr.what(os.path.join("./JPEGImages", imageFileName)):
            continue
        tree = ET.parse(filePath)
        root = tree.getroot()
        for objectInfo in root.findall('object'):
            bbox = objectInfo.find('bndbox')
            xmin = int(bbox.find('xmin').text)
            ymin = int(bbox.find('ymin').text)
            xmax = int(bbox.find('xmax').text)
            ymax = int(bbox.find('ymax').text)
            objectSize = (xmax - xmin) * (ymax - ymin)
            if objectSize >= sizeRange[0] and objectSize <= sizeRange[1]:
                dstDir = str(sizeRange[0]) + "to" + str(sizeRange[1])
                if not os.path.exists(dstDir):
                    os.makedirs(os.path.join(dstDir, "Annotations"))
                    os.makedirs(os.path.join(dstDir, "JPEGImages"))
                xmlFileName = filePath.split("\\")[-1][:-4] + ".xml"
                shutil.copyfile(filePath, os.path.join(dstDir,"Annotations", xmlFileName))
                shutil.copyfile(os.path.join("./JPEGImages", imageFileName), os.path.join(dstDir, "JPEGImages", imageFileName))
                break

def xml2coco(xmlFiles, jsonFile):
    categories = {"uav": 1, "bird": 2}
    bndId = 1
    jsonDict = {"images": [], "type": "instances",
                "annotations": [], "categories": []}
    for filePath in tqdm(xmlFiles):
        tree = ET.parse(filePath)
        root = tree.getroot()
        fileName = root.find('filename').text
        imageId = int(os.path.splitext(fileName)[0])
        size = root.find('size')
        width = int(size.find('width').text)
        height = int(size.find('height').text)
        image = {'file_name': fileName, 'height': height,
                 'width': width, 'id': imageId}
        jsonDict['images'].append(image)
        for objectInfo in root.findall('object'):
            category = objectInfo.find('name').text
            if category not in categories:
                print("%s does not exist in categories!")
                os._exit()
            categoryId = categories[category]
            bbox = objectInfo.find('bndbox')
            xmin = int(bbox.find('xmin').text) - 1
            ymin = int(bbox.find('ymin').text) - 1
            xmax = int(bbox.find('xmax').text)
            ymax = int(bbox.find('ymax').text)
            assert(xmax > xmin)
            assert(ymax > ymin)
            objectWidth = abs(xmax - xmin)
            objectHeight = abs(ymax - ymin)
            annotation = {'area': objectWidth*objectHeight,
                          'iscrowd': 0,
                          'image_id': imageId,
                          'bbox': [xmin, ymin, objectWidth, objectHeight],
                          'category_id': categoryId,
                          'id': bndId,
                          'ignore': 0,
                          'segmentation': []}
            jsonDict['annotations'].append(annotation)
            bndId = bndId + 1
    for category, categoryId in categories.items():
        cat = {'supercategory': 'none', 'id': category, 'name': categoryId}
        jsonDict['categories'].append(cat)

    json_fp = open(jsonFile, 'w')
    json_str = json.dumps(jsonDict)
    json_fp.write(json_str)
    json_fp.close()


if __name__ == '__main__':
    os.chdir("./Desktop/bird/bird/")

    xmlFiles = glob.glob('./Annotations/*.xml')
    sizeRange = [4000, 100000]
    selectObjectBySize(sizeRange, xmlFiles)

    #jsonFile = sys.argv[1]
    #xml2coco(xmlFiles)

    #xmlFilePath = "./4000to20000/Annotations/000103.xml"
    #showBBox(xmlFilePath)
