
bl_info = {
    "name": "Autosave",
    "author": "Zigatronz",
    "version": (0, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Sidebar > Autosave Tab",
    "description": "Autosave with custom save path and timer",
    "warning": "",
    "doc_url": "",
    "category": "3D View",
}


import bpy
from bpy.types import Operator, Panel, PropertyGroup
from bpy.props import StringProperty, IntProperty
from bpy.app.handlers import persistent
import ntpath, os, datetime, tempfile, time, shutil
from pathlib import Path

# Handler function to be called by the timer
@persistent
def GetParentDir(path):
    path = Path(path)
    return path.parent.absolute()

def autosave_handler(dummy):
    curSavePath = bpy.data.filepath
    file_name_format : str = bpy.context.scene.autosave_properties.file_name_format
    max_saves : int = bpy.context.scene.autosave_properties.max_saves

    # Make sure that file_name_format is not empty
    if not file_name_format:
        print("autosave: autosave_handler: file_name_format can't be empty!")
        return

    # Custom save path
    YYYY = str(datetime.datetime.now().year).zfill(4)
    MM = str(datetime.datetime.now().month).zfill(2)
    DD = str(datetime.datetime.now().day).zfill(2)
    hour = str(datetime.datetime.now().hour).zfill(2)
    min = str(datetime.datetime.now().minute).zfill(2)
    sec = str(datetime.datetime.now().second).zfill(2)

    save_path =  file_name_format.replace("<YYYY>", YYYY)
    save_path =         save_path.replace("<MM>", MM)
    save_path =         save_path.replace("<DD>", DD)
    save_path =         save_path.replace("<hh>", hour)
    save_path =         save_path.replace("<mm>", min)
    save_path =         save_path.replace("<ss>", sec)
    save_path =         save_path + ".blend"

    # Get save path
    if curSavePath:
        # Blend already save, autosave on the same folder
        curFilename = os.path.splitext(ntpath.basename(curSavePath))[0]
        ParentDir = GetParentDir(curSavePath)
        save_path = os.path.join(ParentDir, curFilename, save_path)
    else:
        # Blend not save yet, autosave on temp folder
        save_path = os.path.join(tempfile.gettempdir(), "Blender Autosave", save_path)
    
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
        blend_files = {}
        # Get filename with modify time
        for file in os.listdir(GetParentDir(save_path)):
            filename = os.fsdecode(file)
            if filename.endswith(".blend"):
                filepath = os.path.join(GetParentDir(save_path), filename)
                blend_files[filepath] = time.ctime(os.path.getmtime(filepath))
        # Keep removing till blend_files is less than max_saves
        while len(blend_files) > max_saves:
            # Sort oldest to "bottom"
            blend_files = dict(sorted(blend_files.items(), key=lambda item: datetime.strptime(item[1], '%a %b %d %H:%M:%S %Y'), reverse=True))
            # Delete oldest file
            old_file = blend_files.popitem()
            os.remove(old_file)


# Panel class for the UI
class AUTOSAVE_PT_main_panel(Panel):
    bl_label = "Autosave"
    bl_idname = "AUTOSAVE_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Autosave'

    # Draw the UI elements
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        autosave_properties = scene.autosave_properties

        # Add a file format for the save path
        layout.prop(autosave_properties, "file_name_format")
        # Add an integer input for the timer
        layout.prop(autosave_properties, "timer")
        # Add an integer input for the max saves
        layout.prop(autosave_properties, "max_saves")

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
        autosave_handler(None)
        self.report({'INFO'}, f"Saved")

        return {'FINISHED'}


# Operator class for the start/stop button
class AUTOSAVE_OT_operator(Operator):
    bl_label = "Start Autosave"
    bl_idname = "wm.autosave_operator"
    bl_description = "Start Autosaving"

    def execute(self, context):
        scene = context.scene
        autosave_properties = scene.autosave_properties
        timer = autosave_properties.timer

        # If the handler is not already registered, register it with the specified time interval
        if not bpy.app.timers.is_registered(autosave_handler):
            bpy.app.timers.register(autosave_handler, first_interval=timer*60)
            self.bl_label = "Stop Autosave"
            self.bl_description = "Stop Autosaving"
            self.report({'INFO'}, f"Autosave started: Saving every {timer} minutes")
        else:
            # If the handler is already registered, unregister it to stop the autosave
            bpy.app.timers.unregister(autosave_handler)
            self.bl_label = "Start Autosave"
            self.bl_description = "Start Autosaving"
            self.report({'INFO'}, f"Autosave stopped")

        return {'FINISHED'}


# Property group class for the autosave properties
class AutosaveProperties(PropertyGroup):
    # Save path property with a file path selector
    file_name_format: StringProperty(
        name="Save Filename Format",
        description="Custom format for filename. Use <YYYY>, <MM>, <DD>, <hh>, <mm>, <ss>",
        default="<YYYY>-<MM>-<DD> <hh>-<mm>-<ss>",
        maxlen=512
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
        description="Max save files",
        default=5,
        min=1,
        soft_max=10
    )

# List of classes to register/unregister
classes = [
    AUTOSAVE_PT_main_panel,
    AUTOSAVE_OT_operator,
    AUTOSAVE_DEMAND_operator,
    AutosaveProperties
]

def register():
    # Register all classes and add the autosave properties to the scene
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.autosave_properties = bpy.props.PointerProperty(type=AutosaveProperties)
    
def unregister():
    # Unregister all classes and remove the autosave properties from the scene
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
if __name__ == "__main__":
    register()

