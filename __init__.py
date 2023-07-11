
bl_info = {
    "name": "Blender ASB",
    "author": "Zigatronz",
    "version": (0, 2, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Autosave Tab",
    "description": "Autosave with custom save path and timer",
    "warning": "",
    "wiki_url": "https://github.com/Zigatronz/Blender-ASB",
    "doc_url": "https://github.com/Zigatronz/Blender-ASB",
    "tracker_url": "https://github.com/Zigatronz/Blender-ASB/issues",
    "category": "3D View",
}


import bpy
from bpy.types import Operator, Panel, PropertyGroup, AddonPreferences
from bpy.props import StringProperty, IntProperty
from bpy.app.handlers import persistent
import ntpath, os, datetime, tempfile, time, shutil
from pathlib import Path

@persistent
def IsFilePathMatchFormat(file_path : str, format : str, fixed_formats : dict, variable_formats = ['<YYYY>', '<MM>', '<DD>', '<hh>', '<mm>', '<ss>']):
    new_file_path = format
    for key, value in fixed_formats.items():
        new_file_path = new_file_path.replace(key, value)
    for value in variable_formats:
        new_file_path = new_file_path.replace(value, (len(value) - 2) * '*')
    if len(file_path) != len(new_file_path):
        return False

    file_path_arr = list(file_path)
    new_file_path_arr = list(new_file_path)
    for i in range(len(file_path_arr)):
        if new_file_path_arr[i] != '*':
            if new_file_path_arr[i] != file_path_arr[i]:
                return False
    
    return True

# Basically get parent path
def GetParentDir(path):
    path = Path(path)
    return path.parent.absolute()

# Perform autosave
def autosave_handler():
    curSavePath = bpy.data.filepath
    preferences = bpy.context.preferences.addons[__name__].preferences
    file_path_format : str = preferences.file_path_format
    max_saves : int = preferences.max_saves
    timerSeconds : int = preferences.timer * 60

    # Make sure that file_path_format is not empty
    if not file_path_format:
        print("autosave: autosave_handler: file_path_format can't be empty!")
        return timerSeconds

    # Custom save path
    TempDir   = str( tempfile.gettempdir() )
    ParentDir = str( GetParentDir(curSavePath) )
    Filename  = str( os.path.splitext(ntpath.basename(curSavePath))[0] )
    YYYY      = str( datetime.datetime.now().year     ).zfill(4)
    MM        = str( datetime.datetime.now().month    ).zfill(2)
    DD        = str( datetime.datetime.now().day      ).zfill(2)
    hour      = str( datetime.datetime.now().hour     ).zfill(2)
    min       = str( datetime.datetime.now().minute   ).zfill(2)
    sec       = str( datetime.datetime.now().second   ).zfill(2)

    save_path =  file_path_format.replace("<TempDir>", TempDir)
    if curSavePath:
        save_path =         save_path.replace("<ParentDir>", ParentDir)
        save_path =         save_path.replace("<Filename>", Filename)
    else:
        save_path =         save_path.replace("<ParentDir>", TempDir)
        save_path =         save_path.replace("<Filename>", "Untitled")
    save_path =         save_path.replace("<YYYY>", YYYY)
    save_path =         save_path.replace("<MM>", MM)
    save_path =         save_path.replace("<DD>", DD)
    save_path =         save_path.replace("<hh>", hour)
    save_path =         save_path.replace("<mm>", min)
    save_path =         save_path.replace("<ss>", sec)
    
    # Make sure that the save_path is good
    if not os.path.exists(GetParentDir(GetParentDir(save_path))):
        print('autosave: autosave_handler: something wrong with file_path_format : "' + save_path + '"')
        return timerSeconds

    # Do not overwrite and save if there's no save_path
    if save_path and not os.path.exists(save_path):
        # Create parent dir if it's not exist
        if not os.path.exists(GetParentDir(save_path)):
            os.mkdir(GetParentDir(save_path))
        # Autosave but don't change/save to main
        if curSavePath:
            # backup
            if os.path.exists(curSavePath + ".old"):
                os.remove(curSavePath + ".old")
            shutil.move(curSavePath, curSavePath + ".old")
            # save to main
            bpy.ops.wm.save_as_mainfile(filepath=curSavePath)
            # perform autosave
            shutil.move(curSavePath, save_path)
            # restore backup
            shutil.move(curSavePath + ".old", curSavePath)
        else:
            bpy.ops.wm.save_as_mainfile(filepath=save_path)

        # Remove oldest blend upon for max_saves
        if max_saves:
            blend_files = {}
            fixed_formats = {
                "<TempDir>" : TempDir,
                "<ParentDir>" : ParentDir,
                "<Filename>" : Filename
            }
            # Get filename with modify time
            for file in os.listdir(GetParentDir(save_path)):
                filepath = os.path.join(GetParentDir(save_path), os.fsdecode(file))
                if IsFilePathMatchFormat(filepath, file_path_format, fixed_formats):
                    blend_files[filepath] = time.ctime(os.path.getmtime(filepath))
            # Keep removing till blend_files is less than max_saves
            while len(blend_files) > max_saves:
                # Sort oldest to "bottom"
                blend_files = dict(sorted(blend_files.items(), key=lambda item: datetime.datetime.strptime(item[1], '%a %b %d %H:%M:%S %Y'), reverse=True))
                # Delete oldest file
                old_file = blend_files.popitem()
                os.remove(str(old_file[0]))
    return timerSeconds


# Panel class for the UI
class AUTOSAVE_PT_main_panel(Panel):
    bl_label = "Blender ASB"
    bl_idname = "AUTOSAVE_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Blender ASB'

    # Draw the UI elements
    def draw(self, context):
        layout = self.layout

        # Add a button to start/stop the autosave
        row = layout.row()
        row.operator("wm.autosave_operator")
        row.operator("wm.autosave_demand_operator")


# Operator class for demand save
class AUTOSAVE_DEMAND_operator(Operator):
    bl_label = "Save Now"
    bl_idname = "wm.autosave_demand_operator"
    bl_description = "Save on your demand (for testing)"

    def execute(self, context):
        # Call save on demand
        autosave_handler()
        self.report({'INFO'}, f"Saved")

        return {'FINISHED'}

# Autosave timer function
def AutosaveTimer(timer):
    if timer > 0:
        if not bpy.app.timers.is_registered(autosave_handler):
            bpy.app.timers.register(autosave_handler, first_interval=timer*60)
    else:
        if bpy.app.timers.is_registered(autosave_handler):
            bpy.app.timers.unregister(autosave_handler)

# Operator class for the start/stop button
class AUTOSAVE_OT_operator(Operator):
    bl_label = "Start Autosave"
    bl_idname = "wm.autosave_operator"
    bl_description = "Start/Stop Autosave"

    def execute(self, context):
        preferences = bpy.context.preferences.addons[__name__].preferences
        timer = preferences.timer

        # If the handler is not already registered, register it with the specified time interval
        if not bpy.app.timers.is_registered(autosave_handler):
            AutosaveTimer(timer)
            self.report({'INFO'}, f"Autosave started: Saving every {timer} minutes")
        else:
            # If the handler is already registered, unregister it to stop the autosave
            AutosaveTimer(0)
            self.report({'INFO'}, f"Autosave stopped")

        return {'FINISHED'}

class AUTOSAVE_Preferences(AddonPreferences):
    bl_idname = __name__
    # Save path property with a file path selector
    file_path_format: StringProperty(
        name="Save Filename Format",
        description="Custom format for filename.\n  Use: \n    <TempDir> : Temporary folder path\n    <ParentDir> : Parent path of saved blend if not this will be replace by Temporary folder\n    <Filename> : Blend filename without extension if not 'Untitled'\n    <YYYY> : 4 digits year\n    <MM> : 2 digits month\n    <DD> : 2 digits day\n    <hh> : 2 digits hour\n    <mm> : 2 digits minuit\n    <ss> : 2 digits second",
        default="<ParentDir>\<Filename>\<Filename>-<YYYY>-<MM>-<DD>_<hh>-<mm>-<ss>.blend",
        maxlen=1024
    )

    # Timer property with an integer input
    timer: IntProperty(
        name="Timer (minutes)",
        description="Time interval between saves in minutes",
        default=1,
        min=1,
        soft_max=10
    )

    # Max saves property with an integer input
    max_saves: IntProperty(
        name="Max Saves",
        description="Max save files\n 0 : no limit",
        default=5,
        min=0,
        soft_max=10
    )

    # Setup layout to draw
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "file_path_format")
        layout.prop(self, "timer")
        layout.prop(self, "max_saves")

# List of classes to register/unregister
classes = [
    AUTOSAVE_PT_main_panel,
    AUTOSAVE_OT_operator,
    AUTOSAVE_DEMAND_operator,
    AUTOSAVE_Preferences
]

# Turn on AutosaveTimer for startup purpose
def AutosaveTimer_On():
    preferences = bpy.context.preferences.addons[__name__].preferences
    timer = preferences.timer
    AutosaveTimer(timer)

def register():
    # Register all classes and add the autosave properties to the scene
    for cls in classes:
        bpy.utils.register_class(cls)
    # Run upon register
    AutosaveTimer_On()
    
def unregister():
    AutosaveTimer(0)
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
if __name__ == "__main__":
    register()

# Run at blender start, give some times for blender to fully load addon
bpy.app.timers.register(AutosaveTimer_On, first_interval=3, persistent=True)
