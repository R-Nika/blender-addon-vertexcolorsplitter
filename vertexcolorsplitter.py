import bpy
import bmesh

bl_info = {
    "name": "Separate by Vertex Color",
    "blender": (3, 6, 0),  # Update this to your Blender version
    "category": "Object",
    "author": "Nika.",
    "version": (1, 0, 1),
    "description": "Separates mesh into objects based on vertex color.",
    "support": "COMMUNITY",
    "warning": "",
}

class OBJECT_OT_separate_by_vertex_color(bpy.types.Operator):
    bl_idname = "object.separate_by_vertex_color"
    bl_label = "Separate by Vertex Color"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.object  # Automatically selects the active object
        if not obj:
            self.report({'ERROR'}, "No object selected.")
            return {'CANCELLED'}

        # If "Merge by Distance" is enabled, run the merge operation
        if context.scene.merge_by_distance:
            bpy.ops.object.mode_set(mode='EDIT')  # Switch to edit mode
            bpy.ops.mesh.select_all(action='SELECT')  # Select all vertices
            threshold = context.scene.merge_distance_threshold
            bpy.ops.mesh.remove_doubles(threshold=threshold)  # Correct operator for Blender 3.6
            bpy.ops.object.mode_set(mode='OBJECT')  # Switch back to object mode
            self.report({'INFO'}, f"Merged vertices by distance ({threshold})")

        # Ensure we're in object mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # Access mesh data
        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)

        # Get the active vertex color layer
        color_layer = bm.loops.layers.color.active
        if not color_layer:
            self.report({'ERROR'}, "No vertex color layer found!")
            return {'CANCELLED'}
        
        # Group faces by their dominant vertex color
        color_faces = {}
        for face in bm.faces:
            # Use the average color of the face as its "dominant" color
            face_color = [
                sum(loop[color_layer][i] for loop in face.loops) / len(face.loops)
                for i in range(4)  # RGBA channels
            ]
            color = tuple(round(c, 3) for c in face_color)  # Round to reduce precision issues
            color_faces.setdefault(color, []).append(face)

        # Create new objects for each color
        for color, faces in color_faces.items():
            # Create a new mesh and object
            new_mesh = bpy.data.meshes.new(f"{obj.name}_{color}")
            new_obj = bpy.data.objects.new(new_mesh.name, new_mesh)
            bpy.context.collection.objects.link(new_obj)

            # Copy location, rotation, and scale
            new_obj.location = obj.location
            new_obj.rotation_euler = obj.rotation_euler
            new_obj.scale = obj.scale

            # Create a new bmesh for the new object
            bm_new = bmesh.new()
            vert_map = {}  # Map original vertices to new vertices
            loop_colors = []  # Store loop colors for new faces

            for face in faces:
                verts = []
                for loop in face.loops:
                    vert = loop.vert
                    if vert not in vert_map:
                        vert_map[vert] = bm_new.verts.new(vert.co)
                    verts.append(vert_map[vert])
                    loop_colors.append(loop[color_layer])  # Store the vertex color for this loop
                bm_new.faces.new(verts)

            # Write new geometry to the mesh
            bm_new.to_mesh(new_mesh)
            bm_new.free()

            # Add vertex color to the new object
            new_mesh.vertex_colors.new(name="Col")  # Create a new vertex color layer
            new_color_layer = new_mesh.vertex_colors["Col"].data

            # Assign vertex colors to the new mesh
            for i, color_data in enumerate(loop_colors):
                new_color_layer[i].color = color_data[:4]  # Assign RGBA

            # Create and assign a material to display vertex colors
            mat = bpy.data.materials.new(name=f"Material_{color}")
            mat.use_nodes = True

            # Get the node tree of the material
            nodes = mat.node_tree.nodes
            links = mat.node_tree.links

            # Clear default nodes
            for node in nodes:
                nodes.remove(node)

            # Create necessary nodes
            material_output = nodes.new(type="ShaderNodeOutputMaterial")
            material_output.location = (400, 0)
            principled_node = nodes.new(type="ShaderNodeBsdfPrincipled")
            principled_node.location = (0, 0)
            vertex_color_node = nodes.new(type="ShaderNodeVertexColor")
            vertex_color_node.location = (-400, 0)
            vertex_color_node.layer_name = "Col"

            # Set Principled BSDF properties for shininess
            principled_node.inputs["Roughness"].default_value = 0.5  # Adjust for desired shininess
            principled_node.inputs["Specular"].default_value = 0.5  # Specular intensity

            # Link nodes
            links.new(vertex_color_node.outputs["Color"], principled_node.inputs["Base Color"])
            links.new(principled_node.outputs["BSDF"], material_output.inputs["Surface"])

            # Assign material to the object
            new_obj.data.materials.append(mat)

            # If Limited Dissolve is enabled, apply it to the new object
            if context.scene.limited_dissolve:
                bpy.context.view_layer.objects.active = new_obj  # Set the new object as active
                bpy.ops.object.mode_set(mode='EDIT')  # Switch to edit mode
                bpy.ops.mesh.select_all(action='SELECT')  # Select all vertices
                angle_limit = context.scene.limited_dissolve_degrees * (3.14159 / 180)  # Convert degrees to radians
                bpy.ops.mesh.dissolve_limited(angle_limit=angle_limit)  # Apply limited dissolve
                bpy.ops.object.mode_set(mode='OBJECT')  # Switch back to object mode
                self.report({'INFO'}, f"Applied Limited Dissolve with {context.scene.limited_dissolve_degrees} degrees to {new_obj.name}")

        # Hide the original object
        obj.hide_set(True)  # Hide in viewport
        obj.hide_render = True  # Hide in render

        self.report({'INFO'}, f"Separated mesh into {len(color_faces)} objects with vertex colors.")
        bm.free()
        return {'FINISHED'}

class VIEW3D_PT_separate_by_vertex_color_panel(bpy.types.Panel):
    bl_label = "Separate by Vertex Color"
    bl_idname = "VIEW3D_PT_separate_by_vertex_color"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'  # Add the panel to the Tool tab

    def draw(self, context):
        layout = self.layout

        # Add the operator button to the panel
        layout.operator(OBJECT_OT_separate_by_vertex_color.bl_idname)

        # Add checkbox for Merge by Distance
        layout.prop(context.scene, "merge_by_distance", text="Merge by Distance")
        
        # Add Merge Distance Threshold, only visible when Merge by Distance is enabled
        if context.scene.merge_by_distance:
            layout.prop(context.scene, "merge_distance_threshold", text="Merge Threshold")
        
        # Add checkbox for Limited Dissolve
        layout.prop(context.scene, "limited_dissolve", text="Limited Dissolve")
        
        # Add value input for degrees of Limited Dissolve, only visible if Limited Dissolve is enabled
        if context.scene.limited_dissolve:
            layout.prop(context.scene, "limited_dissolve_degrees", text="Dissolve Degrees")

def register():
    bpy.utils.register_class(OBJECT_OT_separate_by_vertex_color)
    bpy.utils.register_class(VIEW3D_PT_separate_by_vertex_color_panel)

    # Add properties to the scene for the new options
    bpy.types.Scene.merge_by_distance = bpy.props.BoolProperty(
        name="Merge by Distance", 
        description="Enable merging vertices by distance before separating by vertex color", 
        default=False
    )
    bpy.types.Scene.merge_distance_threshold = bpy.props.FloatProperty(
        name="Merge Distance Threshold", 
        description="Threshold for merging vertices by distance", 
        default=0.001, 
        min=0.0
    )
    bpy.types.Scene.limited_dissolve = bpy.props.BoolProperty(
        name="Limited Dissolve", 
        description="Enable limited dissolve", 
        default=False
    )
    bpy.types.Scene.limited_dissolve_degrees = bpy.props.FloatProperty(
        name="Dissolve Degrees", 
        description="The degree for limited dissolve", 
        default=1.0, 
        min=0.0, 
        max=90.0
    )

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_separate_by_vertex_color)
    bpy.utils.unregister_class(VIEW3D_PT_separate_by_vertex_color_panel)

    # Remove properties from the scene
    del bpy.types.Scene.merge_by_distance
    del bpy.types.Scene.merge_distance_threshold
    del bpy.types.Scene.limited_dissolve
    del bpy.types.Scene.limited_dissolve_degrees

if __name__ == "__main__":
    register()
