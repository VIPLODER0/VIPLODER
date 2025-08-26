import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(111, projection='3d')

# Room definitions: (name, x, y, z, dx, dy, dz)
rooms_3d = [
    ("Hall", 0, 33, 0, 15, 12, 10),
    ("Bedroom 1", 0, 21, 0, 10, 12, 10),
    ("Kitchen", 0, 11, 0, 8, 10, 10),
    ("Bedroom 2", 0, -1, 0, 10, 12, 10),
    ("Staircase", 9, -1, 0, 6, 12, 10),
    ("Common Bath", 8, 11, 0, 6, 6, 10),
]

# Draw 3D boxes for each room
def draw_room(ax, x, y, z, dx, dy, dz, name):
    # vertices of the cube
    vertices = [
        [(x,y,z), (x+dx,y,z), (x+dx,y+dy,z), (x,y+dy,z)], # bottom
        [(x,y,z+dz), (x+dx,y,z+dz), (x+dx,y+dy,z+dz), (x,y+dy,z+dz)], # top
        [(x,y,z), (x+dx,y,z), (x+dx,y,z+dz), (x,y,z+dz)], # front
        [(x,y+dy,z), (x+dx,y+dy,z), (x+dx,y+dy,z+dz), (x,y+dy,z+dz)], # back
        [(x,y,z), (x,y+dy,z), (x,y+dy,z+dz), (x,y,z+dz)], # left
        [(x+dx,y,z), (x+dx,y+dy,z), (x+dx,y+dy,z+dz), (x+dx,y,z+dz)], # right
    ]
    ax.add_collection3d(Poly3DCollection(vertices, facecolors='lightblue', linewidths=1, edgecolors='black', alpha=0.6))
    # place name at center top of box
    ax.text(x+dx/2, y+dy/2, z+dz+0.5, name, ha="center", fontsize=8, color="black")

for room in rooms_3d:
    draw_room(ax, room[1], room[2], room[3], room[4], room[5], room[6], room[0])

ax.set_xlim(0, 15)
ax.set_ylim(-2, 46)
ax.set_zlim(0, 12)
ax.set_xlabel("Width (ft)")
ax.set_ylabel("Length (ft)")
ax.set_zlabel("Height (ft)")
ax.set_title("3D View - 15x45 House Plan (2BHK)", fontsize=14)

plt.show()
