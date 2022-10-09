# Import modules
import datetime
import os
import webbrowser
from math import asin, cos, radians, sin, sqrt
from tkinter import (
    Button,
    Entry,
    Frame,
    Label,
    Message,
    OptionMenu,
    StringVar,
    Tk,
    Toplevel,
    filedialog,
)

import gpxpy
import gpxpy.gpx
from xml.etree import ElementTree
import matplotlib.pyplot as plt
import numpy as np

EXTENSION_PREFIX = f"""<gpxtpx:TrackPointExtension xmlns:gpxtpx="http://www.garmin.com/xmlschemas/TrackPointExtension/v1">"""
EXTENSION_POSTFIX = "</gpxtpx:TrackPointExtension>"


class Window:
    def __init__(self, master):

        """Hyperparameters"""
        # How large need the gap to be to be considered as an error ("tracking hole") in your GPX file?
        # By default, a gap means no tracking point for at least 5 sec and 400m of distance.
        self.timeThreshold = 5
        self.distThreshold = 400
        # Resolution of the track when displayed on map. 1 is best resolution, but incredibly slow.
        self.resolution = 5

        """  Define class variables   """
        self.gpx = dict()
        self.gpx["main"] = dict()
        self.gpx["snip"] = dict()
        self.GM_start = "https://www.google.de/maps/dir/"
        self.GM_end = "/data=!4m2!4m1!3e1?hl=en"
        self.path = os.getcwd()

        """ Set up GUI """
        self.master = master
        self.frame = Frame(self.master)
        self.master.minsize(width=800, height=300)
        self.master.wm_title("GPX Track Repair")

        # QUIT Button
        self.b_quit = Button(
            text="QUIT", fg="black", bg="red", command=self.frame.quit
        )
        self.b_quit.grid(row=0, column=0, padx=(10, 150), pady=(10, 50))

        # GPX Path Button
        self.b_gpxUp = Button(
            text="Upload GPX-Track",
            bg="yellow",
            command=lambda: self.trackUpload("main"),
        )
        self.b_gpxUp.grid(row=1, column=1, padx=0, pady=(10, 10), sticky="w")

        # Tracking Mistake Detector Button
        self.b_trackMist = Button(
            text="Show Tracking Mistakes", command=self.trackMistakes
        )
        self.b_trackMist.grid(
            row=1, column=2, padx=(10, 0), pady=(10, 10), sticky="w"
        )
        self.b_trackMist.grid_columnconfigure(0, weight=1)

        # Snippet GPX Upload Button
        self.b_gpxUpSnipp = Button(
            text="Upload GPX fragment",
            bg="yellow",
            command=lambda: self.trackUpload("snip"),
        )
        self.b_gpxUpSnipp.grid(row=2, column=1, padx=0, pady=10, sticky="w")

        # Speed Entry
        self.e_dist = Entry(master)
        self.e_dist.insert(0, "Distance of snippet on GoogleMaps in m")
        self.e_dist.config(width=37)
        self.e_dist.grid(row=2, column=2, padx=(10, 0), pady=10, sticky="w")
        self.e_dist.grid_columnconfigure(1, weight=1)
        self.e_dist.bind("<FocusIn>", self.click_on)

        # Confirmation button for speed submission
        self.b_OK = Button(text="OK", command=self.read_distance)
        self.b_OK.grid(row=2, column=3, padx=(0, 0), pady=10, sticky="w")

        # Merge Button
        self.b_merge = Button(text="Repair!", bg="green", command=self.Merge)
        self.b_merge.grid(row=3, column=1)

    def trackUpload(self, fileType):
        """
        Function that receives the name of the file that is uploaded (main oder snip)
        It opens fileDialog to read in gpx, parses the file, calls the extraction method
        and displays a confirmation window
        """

        # FileDialog, parsing and parameter extraction
        self.gpx[fileType]["path"] = filedialog.askopenfilename(
            parent=root, title="Choose a file"
        )
        self.gpx[fileType]["raw"] = open(self.gpx[fileType]["path"], "r")
        self.gpx[fileType]["parsed"] = gpxpy.parse(self.gpx[fileType]["raw"])

        self.extractParam(fileType)

        # Confirmation window
        self.win_succ = Toplevel(self.master)
        self.win_succ_frame = Frame(self.win_succ)
        self.win_succ.minsize(width=250, height=100)
        self.win_succ.wm_title("Confirmation")
        self.win_succ_mess = Label(
            self.win_succ, text="Upload and parsing of GPS successful"
        )
        self.win_succ_mess.grid(row=1, column=1, padx=20, pady=20)

    def trackMistakes(self):
        """
        Function plotting the list of tracking mistakes. Offers links to GoogleMaps to get the needed
        KML/GPX straight away. You can also choose that you mist the start/end of your ride here
        """

        try:
            self.gpx["main"]["plain"]
        except KeyError:
            self.messageWindow(
                message="File Error, Please upload a valid GPX track (yellow "
                "button) before you try to detect the tracking mistakes.",
                width=250,
                height=150,
            )
            return None

        # Output a window with the tracking mistakes.
        # There is a hyperlink referring to Google/myMaps with every tracking mistake
        self.win_links = Toplevel(self.master)
        self.win_links_frame = Frame(self.win_links)

        # Appearance of window
        self.win_links.minsize(width=500, height=400)

        self.win_links.wm_title("Coordinates of tracking mistakes")

        rows = len(self.gpx["main"]["trackHoles"])
        text = [
            "#",
            "From (Long,Lat)",
            "To (Long,Lat)",
            "Distance (m)",
            'View "#" on GoogleMaps',
        ]
        weights = [1, 2, 2, 2, 3]
        for k in range(len(text)):
            self.win_links.columnconfigure(k, weight=weights[k])
            label = Label(self.win_links, text=text[k]).grid(
                row=0, column=k, pady=10, sticky="w"
            )

        if len(self.gpx["main"]["trackHoles"]) == 0:
            mess = Label(
                self.win_links, text="Great! No error has been found!"
            ).grid(row=1, column=1, pady=10, sticky="w")

        # Display trackHole coordinates
        self.links = []
        run = 0
        for run, errInd in enumerate(self.gpx["main"]["trackHoles"]):
            # Save coordinates of start/end in string
            startLat = str(round(self.gpx["main"]["plain"][errInd - 1, 0], 4))
            startLong = str(round(self.gpx["main"]["plain"][errInd - 1, 1], 4))
            endLat = str(round(self.gpx["main"]["plain"][errInd, 0], 4))
            endLong = str(round(self.gpx["main"]["plain"][errInd, 1], 4))

            num = Label(self.win_links, text=str(run + 1)).grid(
                row=run + 1, column=0, pady=10, sticky="w"
            )

            # Display start end
            start = Label(
                self.win_links, text=(startLat + " , " + startLong)
            ).grid(row=run + 1, column=1, pady=10, sticky="w")
            stop = Label(self.win_links, text=(endLat + " , " + endLong)).grid(
                row=run + 1, column=2, pady=10, sticky="w"
            )

            dist = Label(
                self.win_links,
                text=str(round(self.gpx["main"]["trackHoleSizes"][run], 1)),
            ).grid(row=run + 1, column=3, pady=10, sticky="w")

            self.links.append(
                self.GM_start
                + startLat
                + ","
                + startLong
                + "/"
                + endLat
                + ","
                + endLong
                + self.GM_end
            )

        # For convenience: Put link for mapstogpx
        mapstogpx = Button(
            self.win_links,
            text="GoogleMaps to GPX",
            fg="blue",
            cursor="hand2",
            command=lambda: webbrowser.open_new("https://mapstogpx.com/"),
        )
        mapstogpx.grid(row=run + 3, column=4, pady=30, sticky="w")

        # Buttons to insert snippet at start or end
        missStartString = (
            self.GM_start
            + "/"
            + str(self.gpx["main"]["plain"][0, 0])
            + ","
            + str(self.gpx["main"]["plain"][0, 1])
            + self.GM_end
        )
        missStart = Button(
            self.win_links,
            text="I miss the start of my ride",
            fg="blue",
            cursor="hand2",
            command=lambda: webbrowser.open_new(missStartString),
        )
        missStart.grid(row=run + 3, column=2, pady=10, sticky="w")
        missEndString = (
            self.GM_start
            + str(self.gpx["main"]["plain"][-1, 0])
            + ","
            + str(self.gpx["main"]["plain"][-1, 1])
            + self.GM_end
        )
        missEnd = Button(
            self.win_links,
            text="I miss the end of my ride",
            fg="blue",
            cursor="hand2",
            command=lambda: webbrowser.open_new(missEndString),
        )
        missEnd.grid(row=run + 3, column=3, pady=10, sticky="w")

        # Dropdown menu to create GoogleMapsLink
        tkvar = StringVar(self.win_links)
        popupMenu = OptionMenu(
            self.win_links, tkvar, *list(range(1, len(self.links) + 1))
        )
        popupMenu.grid(row=1, column=4, sticky="w")

        # Confirmation button
        ok_but = Button(
            self.win_links,
            text="GO!",
            fg="blue",
            cursor="hand2",
            command=lambda: webbrowser.open_new(
                self.links[int(tkvar.get()) - 1]
            ),
        )
        ok_but.grid(row=2, column=4, pady=0, sticky="w")

    def extractParam(self, fileType):
        """
        Function extracting basic attributes of the GPX files as well as detecting the mistakes in tracking.
        Objects of type gpxpy.gpx.GPXTrackPoint have attributes of type longitude, latitude, time and elevation
        """

        # Save name of file
        if fileType == "main":
            self.filename = (
                self.gpx["main"]["parsed"]
                .tracks[0]
                .name.strip()
                .replace(" ", "_")
                .replace("/", "_")
                .replace("\\", "_")
                .lower()
            )

        # Allocate space
        self.gpx[fileType]["plain"] = np.zeros(
            (len(self.gpx[fileType]["parsed"].tracks[0].segments[0].points), 4)
        )
        self.gpx[fileType]["trackHoles"] = []
        self.gpx[fileType]["trackHoleSizes"] = []

        # Extract datapoints in easily accessible format (timeDiff to prev, lat, long, elev)
        for track in self.gpx[fileType]["parsed"].tracks:
            for segment in track.segments:
                for ind, point in enumerate(segment.points):
                    # For every GPX point save longitude, latitude and elevation
                    self.gpx[fileType]["plain"][ind, 0] = point.latitude
                    self.gpx[fileType]["plain"][ind, 1] = point.longitude
                    self.gpx[fileType]["plain"][ind, 2] = point.elevation

                    # Save timeDifference to previous step. Absolute time is still complicated to access.
                    if ind > 0 and fileType == "main":
                        timeDiff = (
                            point.time - segment.points[ind - 1].time
                        ).total_seconds()
                        self.gpx[fileType]["plain"][ind, 3] = timeDiff
                        # Save indices of tracking errors
                        if timeDiff > self.timeThreshold:
                            euclid = gpxpy.geo.haversine_distance(
                                point.longitude,
                                point.latitude,
                                segment.points[ind - 1].longitude,
                                segment.points[ind - 1].latitude,
                            )
                            if euclid > self.distThreshold:
                                self.gpx[fileType]["trackHoles"].append(ind)
                                self.gpx[fileType]["trackHoleSizes"].append(
                                    euclid
                                )

        # Save features manually
        if fileType == "main":
            self.gpx[fileType]["startTime"] = (
                self.gpx[fileType]["parsed"]
                .tracks[0]
                .segments[0]
                .points[0]
                .time
            )
            self.gpx[fileType]["finishTime"] = (
                self.gpx[fileType]["parsed"]
                .tracks[0]
                .segments[0]
                .points[-1]
                .time
            )
        self.gpx[fileType]["minLat"] = min(self.gpx[fileType]["plain"][:, 0])
        self.gpx[fileType]["maxLat"] = max(self.gpx[fileType]["plain"][:, 0])
        self.gpx[fileType]["minLong"] = min(self.gpx[fileType]["plain"][:, 1])
        self.gpx[fileType]["maxLong"] = max(self.gpx[fileType]["plain"][:, 1])
        self.gpx[fileType]["minEl"] = min(self.gpx[fileType]["plain"][:, 2])
        self.gpx[fileType]["maxEl"] = max(self.gpx[fileType]["plain"][:, 2])

        return None

    def messageWindow(self, title, message, width, height):
        # Function to open a new small window displaying an error or confirmation message.
        self.win_mess = Toplevel(self.master)
        self.win_mess_frame = Frame(self.win_mess)

        # Appearance of window
        self.win_mess.minsize(width=width, height=height)
        self.win_mess.maxsize(width=800, height=400)
        self.win_mess.wm_title(title)

        # Error message
        self.win_Mess = Message(self.win_mess, text=message)
        self.win_Mess.grid(row=1, column=1, padx=20, pady=20)

    def Merge(self):
        # This function merges the main GPX file with the snippet

        # Error Handling
        try:
            self.dist
        except AttributeError:
            self.messageWindow(
                "Instruction",
                """Please insert a valid distance in m and press the "OK" button.""",
                200,
                100,
            )
            return None
        if self.dist < 0:
            self.messageWindow(
                "Instruction",
                """Please insert a valid distance in m and press the "OK" button.""",
                200,
                100,
            )
            return None

        try:
            self.gpx["main"]["plain"]
        except KeyError:
            self.messageWindow(
                "File Error",
                """Please upload a valid GPX main track before you try to repair it.""",
                200,
                100,
            )
            return None

        try:
            self.gpx["snip"]["parsed"]
        except KeyError:
            self.messageWindow(
                "FileError",
                """Please upload a valid GPX snippet which the programme can use to"""
                + """ repair the main file.""",
                200,
                100,
            )
            return None

        dataOld = self.gpx["main"]["plain"]
        dataNew = self.gpx["snip"]["parsed"].tracks[0].segments[0].points

        var = np.array([dataNew[0].latitude, dataNew[0].longitude])

        np.array(
            [
                self.gpx["snip"]["parsed"]
                .tracks[0]
                .segments[0]
                .points[0]
                .latitude,
                self.gpx["snip"]["parsed"]
                .tracks[0]
                .segments[0]
                .points[0]
                .longitude,
            ]
        )

        # Find the right position of the snippet.
        dists = [
            gpxpy.geo.haversine_distance(
                *np.concatenate((dataOld[ind - 1, 0:2], var)).tolist()
            )
            for ind in self.gpx["main"]["trackHoles"]
        ]

        # In case, the user wants to insert a snippet at the start or the end of the track, we also record these distances.
        self.gpx["main"]["trackHoles"].extend([0, len(dataOld)])
        dists.append(
            gpxpy.geo.haversine_distance(
                *np.concatenate(
                    (
                        dataOld[0, 0:2],
                        np.array([dataNew[-1].latitude, dataNew[-1].longitude]),
                    )
                )
            )
        )
        dists.append(
            gpxpy.geo.haversine_distance(
                *np.concatenate((dataOld[-1, 0:2], var))
            )
        )

        if min(dists) > self.distThreshold:
            self.messageWindow(
                "Data Error",
                """This GPX snippet does not match to file you try to repair.""",
                200,
                100,
            )
            return None

        # Create new GPX file.
        self.new_GPX = gpxpy.gpx.GPX()
        self.new_GPX.nsmap["gpxtpx"] = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
        # Create first track and segment in our GPX:
        gpx_track = gpxpy.gpx.GPXTrack()
        self.new_GPX.tracks.append(gpx_track)
        gpx_segment = gpxpy.gpx.GPXTrackSegment()
        gpx_track.segments.append(gpx_segment)
        self.new_GPX.tracks[0].name = self.filename

        # Original GPX until the error that is smoothed out
        indO = 0
        thresh = self.gpx["main"]["trackHoles"][np.argmin(dists)]
        while indO < thresh:
            point = self.gpx["main"]["parsed"].tracks[0].segments[0].points[indO]
            trackpoint = gpxpy.gpx.GPXTrackPoint(
                dataOld[indO, 0],
                dataOld[indO, 1],
                elevation=dataOld[indO, 2],
                time=point.time,
            )
            indO += 1
            if point.extensions == []:
                continue
            
            # add extensions
            extensions = {}
            for ext in point.extensions:
                for extchild in list(ext):
                    extensions[extchild.tag.split('}')[-1]] = extchild.text
            extension_string = (
                EXTENSION_PREFIX +
                "".join([f"<gpxtpx:{k}>{v}</gpxtpx:{k}>" for k,v in extensions.items()]) +
                EXTENSION_POSTFIX
            )
            gpx_extension = ElementTree.fromstring(extension_string)
            trackpoint.extensions.append(gpx_extension)
            gpx_segment.points.append(trackpoint)
            

        # Compute cumulative time needed for the snippet (in seconds)
        if thresh != len(dataOld) and thresh != 0:  # Regular case
            cum_Time = (
                self.gpx["main"]["parsed"]
                .tracks[0]
                .segments[0]
                .points[thresh + 1]
                .time
                - gpx_segment.points[-1].time
            ).total_seconds()

            # Compute cumulative (pointwise) distance of GPX track and compare to GoogleMaps
            dataNew.append(
                gpx_segment.points[-1]
            )  # To be able to compute distance for first point
            cumDist = 0
            for ind, point in enumerate(dataNew):
                cumDist += gpxpy.geo.haversine_distance(
                    dataNew[ind - 1].latitude,
                    dataNew[ind - 1].longitude,
                    point.latitude,
                    point.longitude,
                )

            self.error = (cumDist / self.dist) - 1

            self.speed = self.dist / cum_Time  # in meters/second
            # Show window to inform about deviation between GM and GPX
            self.messageWindow(
                "Error intensity ",
                """You inserted that the GoogleMaps distance is """
                + str(round(self.dist))
                + """m for this snippet, while the cumulative distance of GPX points is """
                + str(round(cumDist))
                + """m. Therefore the overestimation is """
                + str(round(self.error, 3))
                + """%. The algorithm smoothes this out. The average speed was """
                + str(round(self.speed * 3.6, 2))
                + """km/h.""",
                400,
                200,
            )

        else:  # Special case that we insert sth at beginning or end
            self.speed = 4.16666  # Assuming a pace of 15 km/h.
            if thresh == 0:  # Workaround if we missed the starrt
                t = self.gpx["main"]["parsed"].tracks[0].segments[0].points[
                    0
                ].time - datetime.timedelta(0, self.dist / self.speed)
                gpx_segment.points.append(
                    gpxpy.gpx.GPXTrackPoint(
                        dataNew[0].latitude,
                        dataNew[0].longitude,
                        elevation=dataNew[0].elevation,
                        time=t,
                    )
                )

        # Snippet GPX
        indN = 0
        while indN < len(dataNew) - 1:

            # Compute distance between previous location and this location. Compute how much time this path
            # requires, but compensate with the error such that total time will match the GM distance
            stepDist = gpxpy.geo.haversine_distance(
                gpx_segment.points[-1].latitude,
                gpx_segment.points[-1].longitude,
                dataNew[indN].latitude,
                dataNew[indN].longitude,
            )

            # Skip data point if not futher than 10m away from last
            if stepDist > 10:
                stepTime = stepDist / self.speed
                prevTime = gpx_segment.points[-1].time

                point = dataNew[indN]
                trackpoint = gpxpy.gpx.GPXTrackPoint(
                    point.latitude,
                    point.longitude,
                    elevation=point.elevation,
                    time=prevTime + datetime.timedelta(0, stepTime),
                )

                if point.extensions == []:
                    continue
                
                # add extensions
                extensions = {}
                for ext in point.extensions:
                    for extchild in list(ext):
                        extensions[extchild.tag.split('}')[-1]] = extchild.text
                extension_string = (
                    EXTENSION_PREFIX +
                    "".join([f"<gpxtpx:{k}>{v}</gpxtpx:{k}>" for k,v in extensions.items()]) +
                    EXTENSION_POSTFIX
                )
                gpx_extension = ElementTree.fromstring(extension_string)
                trackpoint.extensions.append(gpx_extension)
                gpx_segment.points.append(trackpoint)


            indN += 1

        # Rest of original GPX
        while indO < len(dataOld):
            point = self.gpx["main"]["parsed"].tracks[0].segments[0].points[indO]
            trackpoint = gpxpy.gpx.GPXTrackPoint(
                dataOld[indO, 0],
                dataOld[indO, 1],
                elevation=dataOld[indO, 2],
                time=point.time,
            )
            indO += 1

            if point.extensions == []:
                continue
            
            # add extensions
            extensions = {}
            for ext in point.extensions:
                for extchild in list(ext):
                    extensions[extchild.tag.split('}')[-1]] = extchild.text
            extension_string = (
                EXTENSION_PREFIX +
                "".join([f"<gpxtpx:{k}>{v}</gpxtpx:{k}>" for k,v in extensions.items()]) +
                EXTENSION_POSTFIX
            )
            gpx_extension = ElementTree.fromstring(extension_string)
            trackpoint.extensions.append(gpx_extension)
            gpx_segment.points.append(trackpoint)


        # DONE. Now save the new file
        self.file = self.new_GPX.to_xml()
        output_dir = os.path.join(os.path.expanduser("~"), "gpxfix")
        os.makedirs(output_dir, exist_ok=True)
        out_path = os.path.join(output_dir, self.filename + "_repaired.gpx")
        f = open(out_path, "w+")
        f.write(self.file)
        f.close()
        # Give confirmation message
        self.messageWindow(
            title="Success!",
            message=f"The track is repaired and saved under {out_path}",
            width=250,
            height=150,
        )

        # Make this file to the new file.
        self.gpx["main"]["parsed"] = self.new_GPX
        self.extractParam("main")

    def read_distance(self):
        # Read out the inserted distance frorm the e_dist field.
        rawDistance = self.e_dist.get()
        try:
            self.dist = float(rawDistance)
        except ValueError:
            self.e_dist.delete(0)
            self.e_dist.insert(0, "Insert a valid number!")
            # If then MERGE is pressed, the latest valid distance value will be used

    def click_on(self, event):
        # Click on an entry. Delete preview text!
        self.e_dist.delete(0)


root = Tk()
gui = Window(root)
root.mainloop()
