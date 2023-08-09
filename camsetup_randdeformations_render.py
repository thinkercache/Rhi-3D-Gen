import bpy
import math
import random
import numpy as np
import json
import os


# Get the head model object
obj = bpy.data.objects["female_head.000"] #replace with male_head.000 if rendering male head model

#-----GENERATE RANDOM "Nose_Derformation_Severity"-----

#our machine supports only about 350 rendering in one run, then it automatically kills program
#hence the following try and except block is added to support the rest of rendering process while skipping the random values which are generated already
#but first skip all the random values that were already considered in the previous run !
# Load the existing random values from the "rand_vals_run1.npy" file
try:
    existing_rand_vals_1 = np.load('rand_vals_run1.npy')
except FileNotFoundError:
    existing_rand_vals_1 = np.array([])

# Load the existing random values from the "rand_vals_run2.npy" file
try:
    existing_rand_vals_2 = np.load('rand_vals_run2.npy')
except FileNotFoundError:
    existing_rand_vals_2 = np.array([])

# Combine the two arrays of existing random values into a single array
existing_rand_vals = np.concatenate((existing_rand_vals_1, existing_rand_vals_2))


# Set the minimum and maximum values for the "Nose_Deformation_Severity" property
min_value = 0.5
max_value = 3.0
rand_lst = []

while len(rand_lst) < 281:
    random_value = random.uniform(min_value, max_value)
    if random_value not in existing_rand_vals:
        rand_lst.append(random_value)

# Save the new list of random values as "rand_vals_run2.npy"
np.save('rand_vals_run3.npy', rand_lst)
   
c = 0
for j in rand_lst:
    # Randomly select a value between the minimum and maximum values
    # random_value = random.uniform(min_value, max_value)

    var_choices = np.array([1, 1, 1])
    deactive = random.sample(range(len(var_choices)), 2) #[random.randint(0, 2) for p in range(0, 2)]
    var_choices[deactive] = 0
    var_choices = var_choices.tolist()

    obj["Nose_Variant_1"] = var_choices[0]
    obj["Nose_Variant_2"] = var_choices[1]
    obj["Nose_Variant_3"] = var_choices[2]

    # Set the value of the "Nose_Deformation_Severity" property to the randomly selected value
    obj["Nose_Deformation_Severity"] = j

    label = ""
    if j > 0 and j < 1:
        label = "Mild" 
    elif j > 1 and j < 2:
        label = "Moderate"
    else:
        label = "Severe"

    #print(str(random_value), label, str(var_choices))



    ########-----CAMERA SET UP ----#####

    # Set the number of cameras to create
    num_cameras = 10

    # Set the radius of the circle
    radius = 60.0

    # Set the height of the cameras above the object
    height = 10.0

    # Set the object to face
    object_to_face = bpy.data.objects["female_head.000"]

    # Calculate the angle between each camera
    angle = math.pi / (num_cameras + 1)

    # Create the cameras
    # Create the cameras if they don't exist
    for i in range(num_cameras):
        camera_name = "Camera" + str(i+1)
        if camera_name not in bpy.data.objects:
            # Calculate the position of the camera
            x = radius * math.sin(angle * (i + 1))
            y = radius * math.cos(angle * (i + 1))
            z = height


     # Create the camera object
            camera = bpy.data.cameras.new(camera_name)
            camera_obj = bpy.data.objects.new(camera_name, camera)

            # Set the camera position and rotation
            camera_obj.location = (x, y, z)
            camera_obj.rotation_euler = (math.pi/2, 0, angle * (i + 1))

            # Add the camera to the scene
            bpy.context.scene.collection.objects.link(camera_obj)

            # Set the camera to look at the object
            camera_obj.constraints.new(type='TRACK_TO')
            camera_obj.constraints["Track To"].target = object_to_face
            camera_obj.constraints["Track To"].track_axis = 'TRACK_NEGATIVE_Z'

        # Print camera name and distance from object
    print("Cameras {}: nose deformation severity = {:.2f}, label = {}, nose variants = {}".format(num_cameras, j, label, var_choices))




    #---------RENDERING BEGINS ------

    #Step-1- Nose_Deformation_Severity will be generated randomly 
    #Step-2- Renders(captures image) for that particular value of Severity 
    #while traversing from camera1 to camera 10 by switching among active/inactive cameras
    #This enables capturing 10 images for 1 value of Nose_Deformation_Severity (for random Nose_Variant)


    # Set the render engine to Blender's built-in Cycles renderer
    bpy.context.scene.render.engine = 'CYCLES'

    # Set the dimensions of the output image
    bpy.context.scene.render.resolution_x = 960 #480
    bpy.context.scene.render.resolution_y = 540 #270

    # Set the output folder for the rendered images
    output_folder = "/female_rendered"
    
    # Define subfolder names
    subfolders = ['images', 'points', 'configu']

    # Create subfolders inside output_folder
    for subfolder in subfolders:
        os.makedirs(os.path.join(output_folder, subfolder), exist_ok=True)

    # Render the scene for each camera with the same severity level
    for i in range(num_cameras):
        # Switch to the current camera
        camera_name = "Camera" + str(i+1)
        bpy.context.scene.camera = bpy.data.objects[camera_name]
        active_camera = bpy.data.objects[camera_name]
        
         # Set the file path for the rendered image
        image_file_path = os.path.join(output_folder, "images", "Nose_Deformation_Severity_" + str(c) + "_" + str(j) + "_Camera_" +"{:05n}".format(i+1) + ".png")

        # Render the image
        bpy.ops.render.render()

        # Save the rendered image to the file path
        bpy.data.images['Render Result'].save_render(image_file_path)
        
        #saving all the important properties in a json file.
        output_dict = {
            "total_num_cameras": str(num_cameras),   # total number of cameras (should be 10)
            "active_camera_name": active_camera.name,  # active camera name eg. camera 4
            "camera_focal_len": str(active_camera.data.lens),  # camera focal length in millimeters(mm)
            "camera_loc": str(np.array(active_camera.location)),  # camera location in [x, y, z]
            "camera_rot": str(np.array(active_camera.rotation_euler)),  # camera rotation in [Euler(x, y, z)]
            "nose_deformation_severity": j,  # deformation severity value in float eg. 2.489950
            "label": label,  # mild/moderate/severe
            "nose_variants": var_choices,  # out of 3 variants in format [0, 0, 1] means 3 variant is active with deformation. 
        }

        json_file_path = os.path.join(output_folder, "configu", "Nose_Deformation_Severity_" + str(c) + "_" + str(j) + "_Camera_" + "{:05n}".format(i+1) + ".json")
        with open(json_file_path, 'w') as outfile:
            json.dump(output_dict, outfile)
        outfile.close()

        # Set the file path for the .ply file
        ply_file_path = os.path.join(output_folder, "points", "Nose_Deformation_Severity_" + str(c) + "_" + str(j) + ".ply")

        # Export the .ply file
        object_to_face.select_set(True)
        bpy.ops.export_mesh.ply(filepath=ply_file_path, check_existing=True, filter_glob='*.ply', 
        use_ascii=False, use_selection=True, use_mesh_modifiers=True, use_normals=True, 
        use_uv_coords=True, use_colors=True, global_scale=1.0, axis_forward='Y', axis_up='Z')


    print(f"Rendering finished!")

