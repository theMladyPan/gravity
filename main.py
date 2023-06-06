"""
Compute shader with buffers
"""

# pyinstaller.exe .\main.py --add-data "shaders/;shaders/"
import random
import math
from array import array

import arcade
from arcade.gl import BufferDescription

# Window dimensions
WINDOW_WIDTH = 1910
WINDOW_HEIGHT = 1070

WINDOW_WIDTH, WINDOW_HEIGHT = arcade.window_commands.get_display_size()

# Size of performance graphs
GRAPH_WIDTH = 200
GRAPH_HEIGHT = 120
GRAPH_MARGIN = 5


def pow_random(e: float = 2) -> float:
    r = random.random()
    return math.pow(r, e)

class MyWindow(arcade.Window):

    def __init__(self):
        # Call parent constructor
        # Ask for OpenGL 4.3 context, as we need that for compute shader support.
        super().__init__(WINDOW_WIDTH, WINDOW_HEIGHT,
                        "Compute Shader",
                        gl_version=(4, 3),
                        #resizable=True, 
                        fullscreen=False,
                        vsync=False
                        #draw_rate=0.005
                        )
        self.center_window()

        # --- Class instance variables

        # Number of balls to move
        self.num_stars = 20000

        # This has something to do with how we break the calculations up
        # and parallelize them.
        self.group_x = math.ceil(math.sqrt(self.num_stars))
        self.group_y = 1

        # --- Create buffers

        # Format of the buffer data.
        # 4f = position and size -> x, y, z, radius
        # 4x4 = Four floats used for calculating velocity. Not needed for visualization.
        # 4f = color -> rgba
        buffer_format = "4f 4x4 4f"
        # Generate the initial data that we will put in buffer 1.
        # Pick one of these or make your own function
        # initial_data = self.gen_random_space()
        initial_data = self.gen_galaxies_colliding()

        # Create data buffers for the compute shader
        # We ping-pong render between these two buffers
        # ssbo = shader storage buffer object
        self.ssbo_1 = self.ctx.buffer(data=array('f', initial_data))
        self.ssbo_2 = self.ctx.buffer(reserve=self.ssbo_1.size)

        # Attribute variable names for the vertex shader
        attributes = ["in_vertex", "in_color"]
        self.vao_1 = self.ctx.geometry(
            [BufferDescription(self.ssbo_1, buffer_format, attributes)],
            mode=self.ctx.POINTS,
        )
        self.vao_2 = self.ctx.geometry(
            [BufferDescription(self.ssbo_2, buffer_format, attributes)],
            mode=self.ctx.POINTS,
        )

        # --- Create shaders

        # Load in the shader source code
        file = open("shaders/compute_shader.glsl")
        compute_shader_source = file.read()
        file = open("shaders/vertex_shader.glsl")
        vertex_shader_source = file.read()
        file = open("shaders/fragment_shader.glsl")
        fragment_shader_source = file.read()
        file = open("shaders/geometry_shader.glsl")
        geometry_shader_source = file.read()

        # Create our compute shader.
        # Search/replace to set up our compute groups
        compute_shader_source = compute_shader_source.replace("COMPUTE_SIZE_X",
                                                              str(self.group_x))
        compute_shader_source = compute_shader_source.replace("COMPUTE_SIZE_Y",
                                                              str(self.group_y))
        self.compute_shader = self.ctx.compute_shader(source=compute_shader_source)

        # Program for visualizing the balls
        self.program = self.ctx.program(
            vertex_shader=vertex_shader_source,
            geometry_shader=geometry_shader_source,
            fragment_shader=fragment_shader_source,
        )

        # --- Create FPS graph

        # Enable timings for the performance graph
        arcade.enable_timings()

        # Create a sprite list to put the performance graph into
        self.perf_graph_list = arcade.SpriteList()

        # Create the FPS performance graph
        graph = arcade.PerfGraph(GRAPH_WIDTH, GRAPH_HEIGHT, graph_data="FPS")
        graph.center_x = GRAPH_WIDTH / 2
        graph.center_y = self.height - GRAPH_HEIGHT / 2
        self.perf_graph_list.append(graph)

    def on_draw(self):
        # Clear the screen
        self.clear()
        # Enable blending so our alpha channel works
        self.ctx.enable(self.ctx.BLEND)

        # Bind buffers
        self.ssbo_1.bind_to_storage_buffer(binding=0)
        self.ssbo_2.bind_to_storage_buffer(binding=1)

        # Set input variables for compute shader
        # These are examples, although this example doesn't use them
        # self.compute_shader["screen_size"] = self.get_size()
        # self.compute_shader["force"] = force
        # self.compute_shader["frame_time"] = self.run_time

        # Run compute shader
        self.compute_shader.run(group_x=self.group_x, group_y=self.group_y)

        # Draw the balls
        self.vao_2.render(self.program)

        # Swap the buffers around (we are ping-ping rendering between two buffers)
        self.ssbo_1, self.ssbo_2 = self.ssbo_2, self.ssbo_1
        # Swap what geometry we draw
        self.vao_1, self.vao_2 = self.vao_2, self.vao_1

        # Draw the graphs
        self.perf_graph_list.draw()

    def gen_random_space(self):
        radius = 3.0

        for _ in range(self.num_stars):
            # Position/radius

            yield random.random() * WINDOW_WIDTH
            yield random.random() * WINDOW_HEIGHT
            yield random.random() * WINDOW_HEIGHT
            yield radius * random.random()

            # Velocity
            yield 0.0
            yield 0.0
            yield 0.0
            yield 0.0  # vw (padding)

            # Color
            yield 1.0  # r
            yield 1.0  # g
            yield 1.0  # b
            yield 1.0  # a

    def gen_galaxies_colliding(self):
        radius = 1.2

        STARFIELD_RADIUS = 200
        for i in range(self.num_stars):
            # Position/radius
            angle = random.random() * math.pi * 2
            angle2 = random.random() * math.pi * 2
            distance = random.random() * STARFIELD_RADIUS

            # Alternate stars between galaxies
            if i % 4 == 0:
                yield distance * math.cos(angle) - STARFIELD_RADIUS + WINDOW_WIDTH/4
                yield distance * math.sin(angle) + WINDOW_HEIGHT / 2 + 200
            else:
                yield distance * math.cos(angle) + STARFIELD_RADIUS + WINDOW_WIDTH*3/4
                yield distance * math.sin(angle) + WINDOW_HEIGHT / 2
            yield 0#distance * math.sin(angle2)
            yield radius * pow_random(0)

            # Velocity
            if i % 4 == 0:
                yield math.cos(angle + math.pi / 2) * distance / 50 + 2
            else:
                yield math.cos(angle + math.pi / 2) * distance / 50 - 6
            yield math.sin(angle + math.pi / 2) * distance / 50
            yield 0# math.sin(angle2 + math.pi / 2) * distance / 100
            yield 0.0  # vw (padding)

            # Color
            yield 1.0  # r
            yield 1.0  # g
            yield 1.0  # b
            yield 1.0  # a

    def gen_galaxy_rotating(self):
        radius = 1.5

        STARFIELD_RADIUS = 1500
        for _ in range(self.num_stars):
            # Position/radius
            angle = random.random() * math.pi * 2
            distance = pow_random(2) * STARFIELD_RADIUS

            yield distance * math.cos(angle) + WINDOW_WIDTH / 2
            yield distance * math.sin(angle) + WINDOW_HEIGHT / 2
            yield 0 # distance * math.sin(angle)
            yield radius * pow_random(0)

            # Velocity
            yield math.cos(angle + math.pi / 2) * distance / 150
            yield math.sin(angle + math.pi / 2) * distance / 150
            yield 0 # math.sin(angle2 + math.pi / 2) * distance / 100
            yield 0.0  # vw (padding)

            # Color
            yield 1.0  # r
            yield 1.0  # g
            yield 1.0  # b
            yield 1.0  # a


    def gen_galaxy_explode(self):
        
        STARFIELD_RADIUS = 1500
        radius = 3
        for _ in range(self.num_stars):
            # Position/radius
            angle = random.random() * math.pi * 2
            distance = random.random() * STARFIELD_RADIUS

            yield WINDOW_WIDTH / 2
            yield WINDOW_HEIGHT / 2
            yield 0 # distance * math.sin(angle)
            yield radius * random.random()

            # Velocity
            yield math.sin(angle + math.pi / 2) * distance / 20
            yield -math.cos(angle + math.pi / 2) * distance / 20
            yield 0 # math.sin(angle2 + math.pi / 2) * distance / 100
            yield 0.0  # vw (padding)

            # Color
            yield 1.0  # r
            yield 1.0  # g
            yield 1.0  # b
            yield 1.0  # a


app = MyWindow()
arcade.run()
