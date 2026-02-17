# Import modules
import datetime
import os
import webbrowser
from math import asin, cos, radians, sin, sqrt
from tkinter import (
    Button,
    Frame,
    OptionMenu,
    StringVar,
    Tk,
    Toplevel,
    filedialog,
    messagebox,
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
        self.master.minsize(width=900, height=320)
        self.master.wm_title("GPX Track Repair")

        # Main UI container
        self.main = Frame(self.master, padx=20, pady=16)
        self.main.pack(fill="both", expand=True)

        # Top bar
        self.topbar = Frame(self.main)
        self.topbar.pack(fill="x")

        # QUIT Button
        self.b_quit = Button(
            self.topbar, text="QUIT", fg="black", bg="red", command=self.master.quit
        )
        self.b_quit.pack(side="left")

        # Track controls row
        self.track_controls = Frame(self.main)
        self.track_controls.pack(pady=(44, 12))

        # GPX Path Button
        self.b_gpxUp = Button(
            self.track_controls,
            text="Upload GPX-Track",
            bg="yellow",
            command=lambda: self.trackUpload("main"),
        )
        self.b_gpxUp.pack(side="left", padx=(0, 12))

        # Tracking Mistake Detector Button
        self.b_trackMist = Button(
            self.track_controls,
            text="Show Tracking Mistakes",
            command=self.trackMistakes,
        )
        self.b_trackMist.pack(side="left")

        # Snippet controls row
        self.snip_controls = Frame(self.main)
        self.snip_controls.pack(pady=(6, 10))

        # Snippet GPX Upload Button
        self.b_gpxUpSnipp = Button(
            self.snip_controls,
            text="Upload GPX fragment",
            bg="yellow",
            command=lambda: self.trackUpload("snip"),
        )
        self.b_gpxUpSnipp.pack(side="left", padx=(0, 12))

        # Confirmation button for distance submission (opens a modal prompt).
        self.b_OK = Button(
            self.snip_controls, text="Enter Distance", command=self.read_distance
        )
        self.b_OK.pack(side="left")

        # Merge Button row
        self.repair_controls = Frame(self.main)
        self.repair_controls.pack(pady=(8, 0))
        self.b_merge = Button(
            self.repair_controls, text="Repair!", bg="green", command=self.Merge
        )
        self.b_merge.pack()

    def trackUpload(self, fileType):
        """
        Function that receives the name of the file that is uploaded (main oder snip)
        It opens fileDialog to read in gpx, parses the file, calls the extraction method
        and displays a confirmation window
        """

        # FileDialog, parsing and parameter extraction
        self.gpx[fileType]["path"] = filedialog.askopenfilename(
            parent=self.master, title="Choose a file"
        )
        self.gpx[fileType]["raw"] = open(self.gpx[fileType]["path"], "r")
        self.gpx[fileType]["parsed"] = gpxpy.parse(self.gpx[fileType]["raw"])

        self.extractParam(fileType)

        self.messageWindow(
            title="Confirmation",
            message="Upload and parsing of GPS successful",
            width=250,
            height=100,
        )

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

        # Output a compact control window that relies on native dialogs for textual info.
        self.win_links = Toplevel(self.master)
        self.win_links.minsize(width=500, height=180)
        self.win_links.wm_title("Tracking mistakes")

        # Collect tracking holes and links.
        self.links = []
        self.hole_summaries = []
        for run, errInd in enumerate(self.gpx["main"]["trackHoles"]):
            startLat = str(round(self.gpx["main"]["plain"][errInd - 1, 0], 4))
            startLong = str(round(self.gpx["main"]["plain"][errInd - 1, 1], 4))
            endLat = str(round(self.gpx["main"]["plain"][errInd, 0], 4))
            endLong = str(round(self.gpx["main"]["plain"][errInd, 1], 4))
            dist = str(round(self.gpx["main"]["trackHoleSizes"][run], 1))

            self.hole_summaries.append(
                f"Hole #{run + 1}\nFrom: {startLat} , {startLong}\n"
                f"To: {endLat} , {endLong}\nDistance: {dist} m"
            )
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

        # Top controls: selector + actions.
        top_controls = Frame(self.win_links)
        top_controls.pack(pady=(16, 10))

        tkvar = StringVar(self.win_links)
        if self.links:
            tkvar.set("1")
            popupMenu = OptionMenu(top_controls, tkvar, *list(range(1, len(self.links) + 1)))
        else:
            tkvar.set("No holes")
            popupMenu = OptionMenu(top_controls, tkvar, "No holes")
            popupMenu.configure(state="disabled")
        popupMenu.pack(side="left", padx=(0, 8))

        # Open selected hole on Google Maps.
        ok_but = Button(
            top_controls,
            text="GO!",
            fg="blue",
            cursor="hand2",
            command=lambda: self.open_selected_hole(tkvar),
        )
        if not self.links:
            ok_but.configure(state="disabled")
        ok_but.pack(side="left", padx=(0, 8))

        details_but = Button(
            top_controls,
            text="Show details",
            command=lambda: self.show_selected_hole_info(tkvar),
        )
        details_but.pack(side="left")

        # Bottom controls: helper actions.
        bottom_controls = Frame(self.win_links)
        bottom_controls.pack(side="bottom", pady=(10, 16))

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
            bottom_controls,
            text="I miss the start of my ride",
            fg="blue",
            cursor="hand2",
            command=lambda: webbrowser.open_new(missStartString),
        )
        missStart.pack(side="left", padx=(0, 8))
        missEndString = (
            self.GM_start
            + str(self.gpx["main"]["plain"][-1, 0])
            + ","
            + str(self.gpx["main"]["plain"][-1, 1])
            + self.GM_end
        )
        missEnd = Button(
            bottom_controls,
            text="I miss the end of my ride",
            fg="blue",
            cursor="hand2",
            command=lambda: webbrowser.open_new(missEndString),
        )
        missEnd.pack(side="left", padx=(0, 8))

        # For convenience: Put link for mapstogpx
        mapstogpx = Button(
            bottom_controls,
            text="GoogleMaps to GPX",
            fg="blue",
            cursor="hand2",
            command=lambda: webbrowser.open_new("https://mapstogpx.com/"),
        )
        mapstogpx.pack(side="left")

        if self.links:
            messagebox.showinfo(
                "Tracking mistakes",
                f"Found {len(self.links)} hole(s). Use selector + 'Show details' or 'GO!'.",
                parent=self.win_links,
            )
        else:
            messagebox.showinfo(
                "Tracking mistakes",
                "Great! No error has been found!",
                parent=self.win_links,
            )

    def open_selected_hole(self, tkvar):
        if not self.links:
            return None
        try:
            index = int(tkvar.get()) - 1
        except (TypeError, ValueError):
            return None
        if 0 <= index < len(self.links):
            webbrowser.open_new(self.links[index])
        return None

    def show_selected_hole_info(self, tkvar):
        if not self.links:
            messagebox.showinfo(
                "Tracking mistakes",
                "Great! No error has been found!",
                parent=self.win_links,
            )
            return None
        try:
            index = int(tkvar.get()) - 1
        except (TypeError, ValueError):
            return None
        if 0 <= index < len(self.hole_summaries):
            messagebox.showinfo(
                f"Hole #{index + 1}",
                self.hole_summaries[index],
                parent=self.win_links,
            )
        return None

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

        # NOTE: First, we remove points in the file that are duplicates (i.e.,
        # consecutive time points with SAME coordinates. This happens e.g., if
        # a device continues/starts tracking without having GPS signal
        for track in self.gpx[fileType]["parsed"].tracks:
            for segment in track.segments:

                sane, counter = False, 0
                while not sane:
                    sane = True
                    for ind, point in enumerate(segment.points):
                        lat, long = point.latitude, point.longitude
                        if ind > 0 and lat == prev_lat and long == prev_long:
                            segment.remove_point(ind)
                            sane = False
                            counter += 1
                            break
                        prev_lat, prev_long = point.latitude, point.longitude

        print(f"Removed {counter} duplicate points.")

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
                                self.gpx[fileType]["trackHoleSizes"].append(euclid)

        # Save features manually
        if fileType == "main":
            self.gpx[fileType]["startTime"] = (
                self.gpx[fileType]["parsed"].tracks[0].segments[0].points[0].time
            )
            self.gpx[fileType]["finishTime"] = (
                self.gpx[fileType]["parsed"].tracks[0].segments[0].points[-1].time
            )
        self.gpx[fileType]["minLat"] = min(self.gpx[fileType]["plain"][:, 0])
        self.gpx[fileType]["maxLat"] = max(self.gpx[fileType]["plain"][:, 0])
        self.gpx[fileType]["minLong"] = min(self.gpx[fileType]["plain"][:, 1])
        self.gpx[fileType]["maxLong"] = max(self.gpx[fileType]["plain"][:, 1])
        self.gpx[fileType]["minEl"] = min(self.gpx[fileType]["plain"][:, 2])
        self.gpx[fileType]["maxEl"] = max(self.gpx[fileType]["plain"][:, 2])

        return None

    def messageWindow(self, title="Message", message="", width=None, height=None):
        # Use native message boxes for robust text rendering on macOS Tk.
        messagebox.showinfo(title=title, message=message, parent=self.master)

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
            gpxpy.geo.haversine_distance(*np.concatenate((dataOld[-1, 0:2], var)))
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
        self.new_GPX.nsmap[
            "gpxtpx"
        ] = "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"
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
                gpx_segment.points.append(trackpoint)
                continue

            # add extensions
            extensions = {}
            for ext in point.extensions:
                for extchild in list(ext):
                    extensions[extchild.tag.split("}")[-1]] = extchild.text
            extension_string = (
                EXTENSION_PREFIX
                + "".join(
                    [f"<gpxtpx:{k}>{v}</gpxtpx:{k}>" for k, v in extensions.items()]
                )
                + EXTENSION_POSTFIX
            )
            gpx_extension = ElementTree.fromstring(extension_string)
            trackpoint.extensions.append(gpx_extension)
            gpx_segment.points.append(trackpoint)

        # Compute cumulative time needed for the snippet (in seconds)
        if thresh != len(dataOld) and thresh != 0:  # Regular case
            cum_Time = (
                self.gpx["main"]["parsed"].tracks[0].segments[0].points[thresh].time
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
                    indN += 1
                    gpx_segment.points.append(trackpoint)
                    continue

                # add extensions
                extensions = {}
                for ext in point.extensions:
                    for extchild in list(ext):
                        extensions[extchild.tag.split("}")[-1]] = extchild.text
                extension_string = (
                    EXTENSION_PREFIX
                    + "".join(
                        [f"<gpxtpx:{k}>{v}</gpxtpx:{k}>" for k, v in extensions.items()]
                    )
                    + EXTENSION_POSTFIX
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
                gpx_segment.points.append(trackpoint)
                continue

            # add extensions
            extensions = {}
            for ext in point.extensions:
                for extchild in list(ext):
                    extensions[extchild.tag.split("}")[-1]] = extchild.text
            extension_string = (
                EXTENSION_PREFIX
                + "".join(
                    [f"<gpxtpx:{k}>{v}</gpxtpx:{k}>" for k, v in extensions.items()]
                )
                + EXTENSION_POSTFIX
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
        # Read distance via button-only keypad dialog to avoid flaky text entry rendering.
        value = self.ask_distance_via_keypad(None)
        if value is None:
            return None
        self.dist = value
        self.b_OK.configure(text=f"Enter Distance ({self.dist:g} m)")

    def ask_distance_via_keypad(self, initial=None):
        win = Toplevel(self.master)
        win.wm_title("Snippet distance (m)")
        win.resizable(False, False)
        win.transient(self.master)
        win.grab_set()

        state = {"text": "" if initial is None else str(float(initial)).rstrip("0").rstrip(".")}
        result = {"value": None}

        display = Button(
            win,
            text=state["text"] if state["text"] else "0",
            state="disabled",
            disabledforeground="black",
            relief="sunken",
            width=20,
            anchor="e",
        )
        display.grid(row=0, column=0, columnspan=3, padx=10, pady=(10, 6), sticky="ew")

        def refresh():
            display.configure(text=state["text"] if state["text"] else "0")

        def add_char(ch):
            if ch == "." and "." in state["text"]:
                return
            state["text"] += ch
            refresh()

        def backspace():
            state["text"] = state["text"][:-1]
            refresh()

        def clear():
            state["text"] = ""
            refresh()

        def accept():
            raw = state["text"].strip()
            if raw in {"", ".", "-.", "-"}:
                messagebox.showinfo(
                    title="Instruction",
                    message='Please insert a valid distance in m and press "OK".',
                    parent=win,
                )
                return
            try:
                value = float(raw)
            except ValueError:
                messagebox.showinfo(
                    title="Instruction",
                    message='Please insert a valid distance in m and press "OK".',
                    parent=win,
                )
                return
            if value < 0:
                messagebox.showinfo(
                    title="Instruction",
                    message='Please insert a valid distance in m and press "OK".',
                    parent=win,
                )
                return
            result["value"] = value
            win.destroy()

        def cancel():
            win.destroy()

        keypad_rows = [("7", "8", "9"), ("4", "5", "6"), ("1", "2", "3"), (".", "0", "⌫")]
        for r, row in enumerate(keypad_rows, start=1):
            for c, key in enumerate(row):
                if key == "⌫":
                    cmd = backspace
                else:
                    cmd = (lambda ch=key: add_char(ch))
                Button(win, text=key, width=6, command=cmd).grid(
                    row=r, column=c, padx=4, pady=4
                )

        Button(win, text="Clear", width=6, command=clear).grid(
            row=5, column=0, padx=4, pady=(4, 10)
        )
        Button(win, text="Cancel", width=6, command=cancel).grid(
            row=5, column=1, padx=4, pady=(4, 10)
        )
        Button(win, text="OK", width=6, command=accept).grid(
            row=5, column=2, padx=4, pady=(4, 10)
        )

        def on_key(event):
            ch = event.char
            if ch.isdigit():
                add_char(ch)
            elif ch in {".", ","}:
                add_char(".")
            elif event.keysym == "BackSpace":
                backspace()
            elif event.keysym in {"Return", "KP_Enter"}:
                accept()
            elif event.keysym == "Escape":
                cancel()

        win.bind("<Key>", on_key)
        win.focus_force()
        win.wait_window()
        return result["value"]


def launch():
    os.environ.setdefault("TK_SILENCE_DEPRECATION", "1")
    root = Tk()
    Window(root)
    root.mainloop()


if __name__ == "__main__":
    launch()
