import SimpleITK as sitk
import sys
import os
import glob
from .projection import Projection
from .csv_handler import CsvHandler

class ProjectionsHandler(object):

    def __init__(self):
        try:
            self._du = float(
                input("insert du - Single pixel length in mm, u dir\n"))

            self._dv = float(
                input("insert dv - Single pixel length in mm, v dir\n"))

            self._Niso_u = float(
                input("insert Niso_u - Isocenter position, pixel number, u dir\n"))

            self._Niso_v = float(
                input("insert Niso_u - Isocenter position, pixel number, v dir\n"))

        except ValueError:
            print("Error on input format")
            sys.exit()

    def normalize_mha(self):
        inputPath = os.path.join('projections', 'non_normalized')
        output_path = os.path.join(
                'projections',
                'normalized',
                'normalized.mha')

        # Getting MHA name
        path = os.path.join(inputPath, '*.mha')
        listOfMHANames = glob.glob(path)

        # Find it
        if len(listOfMHANames) > 1:
            print("Error, more than one .mha file is present")
            sys.exit()
        else:
            mhaPath = listOfMHANames[0]
            print("\nFound .mha image inside: " + mhaPath)

        # Getting a list of projection objects from csv file
        csvFolder = os.path.join('csv')
        csvHandler = CsvHandler()
        listOfProjectionObjects = csvHandler.get_projection_object_list_from_csv(
            csvFolder)

        # Read
        non_normalized_mha = sitk.ReadImage(mhaPath)

        # Readinfo
        width = non_normalized_mha.GetWidth()
        height = non_normalized_mha.GetHeight()
        depth = non_normalized_mha.GetDepth()
        
        # open a copy
        normalized_mha = sitk.ReadImage(mhaPath)
        
        # assert dimension csv and depth
        if len(listOfProjectionObjects) != depth:
            print("Error csv dim and proj dime aren't the same.")
            sys.exit()

        # Normalize
        for zslice in range(0, depth):

            print("Normalize projection n " + str(zslice+1))

            extractor = sitk.ExtractImageFilter()
            extractor.SetSize([width, height, 0])
            extractor.SetIndex([0, 0, zslice])

            # Extract projection from non_normalized_mha
            image = extractor.Execute(non_normalized_mha)
                
            # normalize it
            image = image * float(1 / listOfProjectionObjects[zslice].io)
            image = sitk.Log(image)
            image = image * float(-1)

            # convert the 2d slice into a 3d volume slice
            slice_vol = sitk.JoinSeries(image)

            # replace the new 3d volume slice into the old position
            normalized_mha = sitk.Paste(normalized_mha, slice_vol, 
                slice_vol.GetSize(), destinationIndex=[0,0,zslice])
        
        sitk.WriteImage(normalized_mha, output_path)
        print(output_path + " successfully writed")
           

    def set_mha_origin_as_isocenter_position(self):
        
        inputPath = os.path.join(
                'projections',
                'normalized',
                'normalized.mha')
        
        output_path = os.path.join(
                'projections',
                'normalized',
                'normalized.mha')

        # read it
        normalized_mha = sitk.ReadImage(inputPath)

        # Image Origin as Isocenter position on ITK reference system.
        # origin_x = - Niso_u * du
        # origin_y = - (Nv - Niso_v - 1) * dv

        # retrieve Nv as image height
        Nv = normalized_mha.GetHeight()
        origin_x = - (self._Niso_u * self._du)
        origin_y = - (Nv - self._Niso_v - 1) * self._dv

        # third dimension doen't matter, we have a stack of 2D slices.
        normalized_mha.SetOrigin([origin_x, origin_y, 0])
        
        # replace normalized mha
        sitk.WriteImage(normalized_mha, output_path)
        print("Updated normalized origin:",origin_x,origin_y,0)


def normalize_projections():
    # Create ProjectionsHandler object
    ph = ProjectionsHandler()

    # Perform normalization
    ph.normalize_mha()

    # Change MHA origin
    ph.set_mha_origin_as_isocenter_position()
