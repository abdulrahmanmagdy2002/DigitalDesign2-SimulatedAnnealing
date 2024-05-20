import random
import math
import time
import argparse
import matplotlib.pyplot as plt
# from PIL import Image, ImageDraw, ImageFont
# import imageio
# import os

def update_hpwl_for_cells(cell_indices, hpwl_list, nets, cell_positions):
    for net_index in cell_indices:
        x_coords = [cell_positions[cell][0] for cell in nets[net_index]]
        y_coords = [cell_positions[cell][1] for cell in nets[net_index]]
        hpwl_list[net_index] = (max(x_coords) - min(x_coords)) + (max(y_coords) - min(y_coords))
    return hpwl_list, sum(hpwl_list)

def initialize_hpwl(nets, cell_positions):
    hpwl = 0
    hpwl_list = []
    for net in nets:
        x_coords = [cell_positions[cell][0] for cell in net]
        y_coords = [cell_positions[cell][1] for cell in net]
        length = (max(x_coords) - min(x_coords)) + (max(y_coords) - min(y_coords))
        hpwl_list.append(length)
        hpwl += length
    return hpwl_list, hpwl

def print_grid(cell_positions, grid_size):
    grid = [['1' for _ in range(grid_size[1])] for _ in range(grid_size[0])]
    for cell, position in cell_positions.items():
        grid[position[0]][position[1]] = '0'
    for row in grid:
        print(" ".join(row))
    print()

def read_netlist(filename):
    with open(filename, 'r') as f:
        grid_size = list(map(int, f.readline().split()[2:]))
        nets = [list(map(int, line.split()[1:])) for line in f.readlines()]
    return grid_size, nets

def initial_placement(cells, grid_size):
    cell_positions = {}
    occupied_positions = set()
    for cell in cells:
        while True:
            pos = (random.randrange(grid_size[0]), random.randrange(grid_size[1]))
            if pos not in occupied_positions:
                cell_positions[cell] = pos
                occupied_positions.add(pos)
                break
    return cell_positions

def create_grid(cell_positions, grid_size):
    grid = [["--" for _ in range(grid_size[1])] for _ in range(grid_size[0])]
    for cell, (row, col) in cell_positions.items():
        grid[row][col] = cell
    return grid

def swap_cells(cell_positions, grid, cell1, cell2, pos1, pos2):
    if cell1 == "--":
        cell_positions[cell2] = pos1
    elif cell2 == "--":
        cell_positions[cell1] = pos2
    else:
        cell_positions[cell1], cell_positions[cell2] = pos2, pos1

# def draw_grid_image(cell_positions, grid_size, file_path):
#     cell_size = 50
#     img = Image.new('RGB', (grid_size[1] * cell_size, grid_size[0] * cell_size), color='white')
#     draw = ImageDraw.Draw(img)
#     font = ImageFont.load_default()

#     for row in range(grid_size[0]):
#         for col in range(grid_size[1]):
#             x0 = col * cell_size
#             y0 = row * cell_size
#             x1 = x0 + cell_size
#             y1 = y0 + cell_size
#             draw.rectangle([x0, y0, x1, y1], outline='black')
#             cell = [key for key, value in cell_positions.items() if value == (row, col)]
#             if cell:
#                 draw.text((x0 + cell_size / 4, y0 + cell_size / 4), f'{cell[0]:02d}', fill='black', font=font)
    
#     img.save(file_path)

def simulated_annealing(filename, cooling_rate, gif_name):
    random.seed(30)
    grid_size, nets = read_netlist(filename)
    
    cells = set(cell for net in nets for cell in net)
    cell_positions = initial_placement(cells, grid_size)
    
    net_indices = {cell: [i for i, net in enumerate(nets) if cell in net] for cell in cells}
    
    hpwl_list, total_hpwl = initialize_hpwl(nets, cell_positions)
    initial_hpwl = total_hpwl
    
    initial_temp = total_hpwl * 500
    final_temp = 5e-6 * total_hpwl / len(nets)
    current_temp = initial_temp
    moves_per_temp = 10 * len(cells)
    
    print(f"Initial Placement (Cooling rate: {cooling_rate}):")
    print_grid(cell_positions, grid_size)
    print("Initial total wire length:", total_hpwl)
    
    temps = []
    hpwls = []
    # images = []
    
    # Create a directory to save images
    # image_dir = "images"
    # if not os.path.exists(image_dir):
    #     os.makedirs(image_dir)
    
    while current_temp > final_temp:
        for _ in range(moves_per_temp):
            cell_positions_copy = cell_positions.copy()
            grid = create_grid(cell_positions_copy, grid_size)
            
            pos1 = (random.randrange(grid_size[0]), random.randrange(grid_size[1]))
            pos2 = (random.randrange(grid_size[0]), random.randrange(grid_size[1]))
            cell1 = grid[pos1[0]][pos1[1]]
            cell2 = grid[pos2[0]][pos2[1]]
            
            while cell1 == cell2 or (cell1 == "--" and cell2 == "--"):
                pos1 = (random.randrange(grid_size[0]), random.randrange(grid_size[1]))
                pos2 = (random.randrange(grid_size[0]), random.randrange(grid_size[1]))
                cell1 = grid[pos1[0]][pos1[1]]
                cell2 = grid[pos2[0]][pos2[1]]
            
            swap_cells(cell_positions_copy, grid, cell1, cell2, pos1, pos2)
            
            if cell1 == "--":
                hpwl_list_copy, new_hpwl = update_hpwl_for_cells(net_indices[cell2], hpwl_list.copy(), nets, cell_positions_copy)
            elif cell2 == "--":
                hpwl_list_copy, new_hpwl = update_hpwl_for_cells(net_indices[cell1], hpwl_list.copy(), nets, cell_positions_copy)
            else:
                affected_nets = list(set(net_indices[cell1] + net_indices[cell2]))
                hpwl_list_copy, new_hpwl = update_hpwl_for_cells(affected_nets, hpwl_list.copy(), nets, cell_positions_copy)
            
            delta_hpwl = new_hpwl - total_hpwl
            if delta_hpwl < 0 or random.uniform(0, 1) < math.exp(-delta_hpwl / current_temp):
                cell_positions = cell_positions_copy
                total_hpwl = new_hpwl
                hpwl_list = hpwl_list_copy
        
        temps.append(current_temp)
        hpwls.append(total_hpwl)
        
        # image_path = os.path.join(image_dir, f"step_{len(images)}.png")
        # draw_grid_image(cell_positions, grid_size, image_path)
        # images.append(imageio.imread(image_path))
        
        current_temp *= cooling_rate
    
    # imageio.mimsave(gif_name, images, duration=0.5)
    
    print(f"Final Placement (Cooling rate: {cooling_rate}):")
    print_grid(cell_positions, grid_size)
    print("Final total wire length:", total_hpwl)
    print("Execution time:", time.time() - start_time, "seconds")
    return grid_size, cell_positions, total_hpwl, initial_hpwl, temps, hpwls

def plot_graphs(temps, hpwls, cooling_rate):
    plt.figure()
    plt.plot(temps, hpwls)
    plt.title(f'Temperature vs. TWL (Cooling rate: {cooling_rate})')
    plt.xlabel('Temperature')
    plt.ylabel('Total Wire Length')
    plt.xscale('log')
    plt.yscale('log')
    plt.show()

def plot_cooling_rate_vs_twl(filename):
    cooling_rates = [0.75, 0.8, 0.85, 0.9, 0.95]
    final_twl = []
    
    for rate in cooling_rates:
        print(f"Running simulated annealing with cooling rate: {rate}")
        # gif_name = f"simulated_annealing_{rate}.gif"
        _, _, final_hpwl, _, _, _ = simulated_annealing(filename, rate, "")
        final_twl.append(final_hpwl)
    
    plt.figure()
    plt.plot(cooling_rates, final_twl, marker='o')
    plt.title('Cooling rate vs. Final TWL')
    plt.xlabel('Cooling Rate')
    plt.ylabel('Final Total Wire Length')
    plt.show()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulated Annealing for Cell Placement")
    parser.add_argument("filename", type=str, help="Path to the netlist file")
    args = parser.parse_args()
    
    start_time = time.time()
    
    filename = args.filename
    cooling_rate = 0.95
    
    print(f"Running simulated annealing with cooling rate: {cooling_rate}")
    grid_size, cell_positions, final_twl, initial_twl, temps, hpwls = simulated_annealing(filename, cooling_rate, "")
    
    print(f"Plotting graphs for cooling rate: {cooling_rate}")
    plot_graphs(temps, hpwls, cooling_rate)
    plot_cooling_rate_vs_twl(filename)
    
    print("Script completed successfully.")
