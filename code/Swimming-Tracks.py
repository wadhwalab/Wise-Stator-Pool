# Fiji/Jython script — must be run from the Fiji Script Editor, not the command line.
# Tracks free-swimming cells using TrackMate and exports per-cell mean speed CSVs.
# Credit: Seiga and Shabduli
import sys
from ij import IJ
from ij import WindowManager
from ij.io import DirectoryChooser
import os
from fiji.plugin.trackmate import Model, Settings, TrackMate, Logger
from fiji.plugin.trackmate.detection import ThresholdDetectorFactory
from fiji.plugin.trackmate.tracking.jaqaman import SimpleSparseLAPTrackerFactory
from fiji.plugin.trackmate.gui.displaysettings import DisplaySettingsIO
from fiji.plugin.trackmate.gui.displaysettings.DisplaySettings import TrackMateObject
from fiji.plugin.trackmate.features.track import TrackIndexAnalyzer
from fiji.plugin.trackmate.action import ExportTracksToXML
from java.io import File
from fiji.plugin.trackmate.action import CaptureOverlayAction
from ij.measure import ResultsTable
from fiji.plugin.trackmate.io import TmXmlReader, TmXmlWriter
import fiji.plugin.trackmate.visualization.hyperstack.HyperStackDisplayer as HyperStackDisplayer
import fiji.plugin.trackmate.features.FeatureFilter as FeatureFilter
from fiji.plugin.trackmate import SelectionModel
from ij.gui import GenericDialog  # Import for creating dialog box

# We have to do the following to avoid errors with UTF8 chars generated in TrackMate that will mess with our Fiji Jython.
reload(sys)
sys.setdefaultencoding('utf-8')

# Ask the user to select the input directory
inputDirChooser = DirectoryChooser("Select input directory")
inputDir = inputDirChooser.getDirectory()

# Check if the user canceled the directory selection
if inputDir is None:
    print("Input directory selection canceled.")
    exit()

# Ask the user to select the output directory
outputDirChooser = DirectoryChooser("Select output directory")
outputDir = outputDirChooser.getDirectory()

# Check if the user canceled the directory selection
if outputDir is None:
    print("Output directory selection canceled.")
    exit()

# Check if the output directory exists, if not create it
if not os.path.exists(outputDir):
    os.makedirs(outputDir)

# Function to create a unique folder name
def create_unique_folder(base_path, folder_name):
    new_folder_path = os.path.join(base_path, folder_name)
    counter = 1
    while os.path.exists(new_folder_path):
        new_folder_path = os.path.join(base_path, "%s (%d)" % (folder_name, counter))
        counter += 1
    os.makedirs(new_folder_path)
    return new_folder_path

# Create the unique output folder
output_folder = create_unique_folder(outputDir, "Track mean speed csv files")

# Get list of files in the input directory
fileList = os.listdir(inputDir)

# Check if the directory is empty
if not fileList:
    print("Input directory is empty.")
    exit()

# Debug print statement
print("Input Directory: {}".format(inputDir))
print("Output Directory: {}".format(outputDir))

# Prompt user for displaying the results video
gd = GenericDialog("Display Results Video")
gd.addCheckbox("Would you like to see the results video?", False)
gd.showDialog()

if gd.wasCanceled():
    print("User canceled the dialog.")
    exit()

show_video = gd.getNextBoolean()

# Write the parameters to a single text file
paramsFilePath = os.path.join(output_folder, "analysis_parameters.txt")
with open(paramsFilePath, 'w') as param_file:
	param_file.write("Analysis Parameters\n")
	param_file.write("===================\n\n")
	
	# Process the files in the input directory
	for file in fileList:
		if file.startswith('.'):  # Skip hidden files like .DS_Store
			continue
			
		print("Processing file: {}".format(file))
		
		
		# Load the video file
		filePath = os.path.join(inputDir, file)
		imp = IJ.openImage(filePath)
		
		
		if imp is None:
		    print("Error loading file: {}".format(file))
		    continue
		
		# Handle image dimensions
		dims = imp.getDimensions()
		imp.setDimensions(dims[2], dims[4], dims[3])
		
		# Convert to 8-bit grayscale
		IJ.run(imp, "8-bit", "")
		
		# Measure intensity
		IJ.run(imp, "Measure", "")
		
		# Get the results table
		results_table = ResultsTable.getResultsTable()
		
		# Get the intensity values from the results table
		intensity_values = results_table.getColumnAsDoubles(results_table.getColumnIndex("Mean"))
		tsh = (intensity_values[-1]) + 15
		
		# Create TrackMate settings
		model = Model()
		model.setLogger(Logger.IJ_LOGGER)
		
		settings = Settings(imp)
		settings.detectorFactory = ThresholdDetectorFactory()
		settings.detectorSettings = {
		    'TARGET_CHANNEL': 1,
		    'INTENSITY_THRESHOLD': tsh,  # Ensure this is a floating-point number
		    'SIMPLIFY_CONTOURS': True
		}
		
		# Configure tracker
		settings.trackerFactory = SimpleSparseLAPTrackerFactory()
		settings.trackerSettings = settings.trackerFactory.getDefaultSettings()
		settings.trackerSettings['LINKING_MAX_DISTANCE'] = 15.0
		settings.trackerSettings['ALLOW_GAP_CLOSING'] = True
		settings.trackerSettings['ALLOW_TRACK_SPLITTING'] = False
		settings.trackerSettings['ALLOW_TRACK_MERGING'] = False
		settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE'] = 50.0
		settings.trackerSettings['MAX_FRAME_GAP'] = 20
		
		# Add feature analyzers and filters
		settings.addAllAnalyzers()
		filter1 = FeatureFilter('CIRCULARITY', 0.5, True)
		settings.addSpotFilter(filter1)
		filter2 = FeatureFilter('AREA', 10.0, True)
		settings.addSpotFilter(filter2)
		filter3 = FeatureFilter('TRACK_DURATION', 15, True)
		settings.addTrackFilter(filter3)
		
		# Run TrackMate
		trackmate = TrackMate(model, settings)
		
		if not trackmate.checkInput():
		    print("Error while checking input for file {}:".format(file))
		    print(trackmate.getErrorMessage())
		    continue
		
		if not trackmate.process():
		    print("Error while processing file {}:".format(file))
		    print(trackmate.getErrorMessage())
		    continue
		
		# Save TrackMate results
		outputFilePath = os.path.join(outputDir, file[:-4] + "_trackmate_results.xml")
		writer = TmXmlWriter(File(outputFilePath))
		
		try:
		    writer.appendModel(model)
		    writer.appendSettings(settings)
		    writer.appendTracks(model)
		    writer.appendImageData(imp)
		    writer.writeToFile()
		except Exception as e:
		    print("Error writing results for file {}: {}".format(file, str(e)))
		
		# Display results if user opted to
		if show_video:
		    selectionModel = SelectionModel(model)
		    ds = DisplaySettingsIO.readUserDefault()
		    ds.setTrackColorBy(TrackMateObject.TRACKS, TrackIndexAnalyzer.TRACK_INDEX)
		    ds.setSpotColorBy(TrackMateObject.TRACKS, TrackIndexAnalyzer.TRACK_INDEX)
		    
		    displayer = HyperStackDisplayer(model, selectionModel, imp, ds)
		    displayer.render()
		    displayer.refresh()
		
		# Echo results with the logger we set at start
		model.getLogger().log(str(model))
		
		fm = model.getFeatureModel()
		
		# Get the results table
		rt = ResultsTable()
		
		# Get the mean speed feature
		mean_speed = 'TRACK_MEAN_SPEED'
		
		# Add mean speed to the results table for each track
		for track_id in model.getTrackModel().trackIDs(True):
		    mean_speed_value = model.getFeatureModel().getTrackFeature(track_id, mean_speed)
		    rt.incrementCounter()
		    rt.setValue("Track_ID", rt.getCounter() - 1, track_id)
		    rt.setValue("Mean_Speed", rt.getCounter() - 1, mean_speed_value)
		
		# Save the results table
		resultsFilePath = os.path.join(output_folder, file[:-4] + ".csv")
		rt.save(resultsFilePath)
		
		print("Finished processing file: {}".format(file))
		param_file.write(file)
		param_file.write("\n")
		param_file.write("INTENSITY_THRESHOLD: {}\n".format(settings.detectorSettings['INTENSITY_THRESHOLD']))
		param_file.write("LINKING_MAX_DISTANCE: {}\n".format(settings.trackerSettings['LINKING_MAX_DISTANCE']))
		param_file.write("GAP_CLOSING_MAX_DISTANCE: {}\n".format(settings.trackerSettings['GAP_CLOSING_MAX_DISTANCE']))
		param_file.write("MAX_FRAME_GAP: {}\n\n".format(settings.trackerSettings['MAX_FRAME_GAP']))
		
		param_file.write("Spot Filters:\n")
		for spot_filter in settings.getSpotFilters():
		    param_file.write(" - {}: (isAbove: {}) {}\n".format(spot_filter.feature, spot_filter.isAbove, spot_filter.value))
		
		param_file.write("\nTrack Filters:\n")
		for track_filter in settings.getTrackFilters():
		    param_file.write(" - {}: (isAbove: {}) {}\n".format(track_filter.feature, track_filter.isAbove, track_filter.value))
        	param_file.write("\n")
print("TrackMate analysis complete.")
