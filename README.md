Separate by Vertex Color Addon for Blender v3.6 STL
=========================================

Overview
--------
This Blender addon is designed to help with the process of separating meshes by their vertex color,
which is particularly useful for **Stormworks modding**. The addon automatically splits a mesh into
multiple objects based on their vertex colors and offers options for additional optimization such as
merging vertices and limited dissolving geometry.

Features
--------
- **Separate Mesh by Vertex Color**: Automatically splits your mesh into objects based on vertex colors.
- **Merge by Distance**: Option to merge vertices within a defined distance to clean up the mesh.
- **Limited Dissolve**: Option to dissolve vertices/edges based on an angle limit to reduce geometry.

Installation
------------
1. Download the addon file.
2. Open Blender.
3. Go to **Edit** > **Preferences** > **Add-ons** > **Install**.
4. Select the downloaded `.py` file.
5. Once installed, enable the addon by checking the box next to it in the Add-ons tab.

Usage
-----
1. Open the **3D Viewport** in Blender.
2. Go to the **Tool** tab on the right sidebar.
3. Find the **Separate by Vertex Color** panel.
4. In **Object Mode** select the object you want to work with.
5. Use the checkboxes:
   - **Merge by Distance**: If you want to merge vertices that are within a specified distance, enable this option.
   - **Limited Dissolve**: If you want to dissolve geometry based on the angle between faces, enable this option and specify the angle limit (default is 1 degree).
6. Click the **Separate by Vertex Color** button to separate the mesh into new objects.
   - If the boolean options are enabled, the merge and dissolve actions will run automatically on the separated objects.

