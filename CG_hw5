#!/usr/bin/env python3

import argparse
import math
from transformers import ThreeDTransformer, TwoDTransformer, Coordinates
from fileIO import FileIO       

class Clip(Coordinates):
    def __init__(self, lines, args, twoDtransformer: TwoDTransformer, threeDtransformer: ThreeDTransformer, is_perspective):
        super().__init__()
        self.is_perspective = is_perspective
        self.lines = lines
        self.args = args
        self.twoDtransformer = twoDtransformer
        self.inside = 0 # 0000
        self.left = 1   # 0001
        self.right = 2  # 0010
        self.bottom = 4 # 0100
        self.top = 8    # 1000
        if not self.is_perspective:
            self.x_min = -abs(threeDtransformer.d)
            self.y_min = -abs(threeDtransformer.d)
            self.x_max = abs(threeDtransformer.d)
            self.y_max = abs(threeDtransformer.d)
            self.z_max = (args.z_prp - threeDtransformer.F) / (threeDtransformer.B - args.z_prp)
        else:
            self.x_min = -1
            self.y_min = -1
            self.x_max = 1
            self.y_max = 1
            self.z_max = 0
        self.u_min = self.args.lb_viewportx
        self.v_min = self.args.lb_viewporty
        self.u_max = self.args.ub_viewportx
        self.v_max = self.args.ub_viewporty
        self.d = threeDtransformer.d
        self.z_min = -1
        
        # print(self.z_max)

    def z_buffering(self, polygons):
        color_index = -1
        # z values that are bigger are closer
        frame_buf = [ [0]*501 for _ in range(501) ]
        z_buf = [ [0]*501 for _ in range(501) ]

        # initialize buffers
        for row in range(501):
            for col in range(501):
                frame_buf[row][col] = "0 0 0"
                z_buf[row][col] = self.z_min
        
        prepared_polygons = self._prepare_polygons(polygons)
        for polygon in prepared_polygons:
            if "new model" not in polygon:
                # converted normalized coordinates to viewport coordinates for scanfill
                viewport_face = self.world_to_viewport(polygon)
                # print(viewport_face)
                scanfill_ds = self._polygon_scan_fill(viewport_face)
                for scan_line, intersecting_edges in scanfill_ds.items():
                    scan_line_edge = self._set_scan_line_edge(scan_line)
                    x_range = self._sort_intersections(scan_line_edge, intersecting_edges, viewport_face)
                    frame_buf, z_buf = self.z_interpolation(x_range, z_buf, frame_buf, scan_line, color_index)
            else:
                color_index += 1

        return frame_buf

    def z_interpolation(self, x_range, z_buf, f_buf, y, color_index):
        za, zb = x_range[0][1], x_range[1][1]
        left_x, right_x = int(x_range[0][0]), int(x_range[1][0])
        
        for x in range(left_x, right_x):
            zp = zb - (zb - za) * ( (right_x - x) / (right_x - left_x) )
            # print(f"{zb} - {zb - za} * {right_x - x} / {right_x - left_x} = {zp}")

            if zp < self.z_max and zp > z_buf[y][x]:
                z_buf[y][x] = zp

                depth_color = round(255 * (zp - self.z_min) / (self.z_max - self.z_min))
                # print(f"{255} * {zp} - {self.z_min} / {self.z_max} - {self.z_min} = {depth_color}")
                if color_index == 0:
                    color = f"{depth_color} 0 0"
                elif color_index == 1:
                    color = f"0 {depth_color} 0"
                elif color_index == 2:
                    color = f"0 0 {depth_color}"
                
                f_buf[y][x] = color
        return f_buf, z_buf

    def world_to_viewport(self, polygons):
        s_x = (self.u_max - self.u_min) / (self.x_max - self.x_min)
        s_y = (self.v_max - self.v_min) / (self.y_max - self.y_min)

        viewport_polygon = []
        # for polygon in polygons:
        for line in polygons:
            if "stroke" in line:
                viewport_polygon.append(line)
            else:
                self.twoDtransformer._set_points(line)
                self.twoDtransformer._translate(self.x_min, self.y_min)
                self.twoDtransformer._scale(s_x, s_y)
                self.twoDtransformer._translate(-self.u_min, -self.v_min)
                # needed to round for scanfill
                viewport_polygon.append([round(abs(self.twoDtransformer.x1)), round(abs(self.twoDtransformer.y1)), line[2]])
        return viewport_polygon

    def _set_scan_line_edge(self, y):
        return [0, y, 500, y]
            
    def _polygon_scan_fill(self, polygon):
        # finds min and max y of polygon face for optimization
        min_y = math.inf
        max_y = -math.inf
        for coordinate in polygon:
            if "stroke" not in coordinate:
                min_y = min(coordinate[1], min_y)
                max_y = max(coordinate[1], max_y)

        scan_line_ys = {}
        for y in range(min_y, max_y):
            edges = []
            for index, line in enumerate(polygon):
                if "new model" in line:
                    continue
                if index+1 < len(polygon) and ("stroke" not in line and "stroke" not in polygon[index+1]):
                    v1 = [line[0], line[1]]
                    v2 = [polygon[index+1][0], polygon[index+1][1]] 
                    y_min = min(v1[1], v2[1])
                    y_max = max(v1[1], v2[1])
                    is_horizontal = y_min - y_max
                    if is_horizontal == 0 or y == y_max:
                        continue
                    if y_min <= y and y < y_max:
                        edges.append([index, index+1])
            scan_line_ys[y] = edges
        return scan_line_ys

    def _sort_intersections(self, scan_line_edge, edges, polygon):
        intersections = []
        for edge in edges:
            intersection = self._compute_intersection(polygon[edge[0]], polygon[edge[1]], scan_line_edge)
            intersections.append([intersection[0], intersection[2]])
        intersections.sort(key=lambda x: x)
        return intersections

    def _compute_intersection(self, v1, v2, edge):
        new_vertex = []
        x1, y1 = v1[0], v1[1]
        x2, y2 = v2[0], v2[1]
        x3, y3 = edge[0], edge[1]
        x4, y4 = edge[2], edge[3]

        x = ( (x1*y2 - y1*x2) * (x3 - x4) - (x1 - x2) * (x3*y4 - y3*x4) ) / ( (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4) )
        y = ( (x1*y2 - y1*x2) * (y3 - y4) - (y1 - y2) * (x3*y4 - y3*x4) ) / ( (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4) )

        new_vertex.append(x)
        new_vertex.append(y)

        # new code to find z value
        ys = edge[1]
        z1, z2 = v1[2], v2[2]
        z = z1 - (z1 - z2) * ( (y1 - ys) / (y1 - y2) )
        # print(f"{z1} - {z1 - z2} * {y1 - ys} / {y1 - y2} = {z}")
        new_vertex.append(z)

        return new_vertex

    def _set_edges(self, x_min, y_min, x_max, y_max):
        edges = []
        # right
        edges.append([x_max, y_min, x_max, y_max, "right"])
        # bottom
        edges.append([x_min, y_min, x_max, y_min, "bottom"])
        # left
        edges.append([x_min, y_min, x_min, y_max, "left"])
        # top
        edges.append([x_min, y_max, x_max, y_max, "top"])

        return edges

    def _prepare_polygons(self, lines):
        polygons = []
        polygon = []
        for i in lines:
            if "new model" in i:
                polygons.append(i)
            elif "stroke" not in i:
                polygon.append(i)
            else:
                polygon.append(i)
                polygons.append(polygon)
                polygon = []
        return polygons

def hw5(args):
    fileio = FileIO(args.red_file, args.green_file, args.blue_file)
    faces = fileio.read_smf()

    # for i in faces:
    #     print(i)

    threeDtransformer = ThreeDTransformer(faces, args)
    if args.projection:
        polygon = threeDtransformer.parallel_normalization()
    else: 
        polygon = threeDtransformer.perspective_normalization()
    
    # print('newlines')
    # for i in polygon:
    #     print(i)

    twoDtransformer = TwoDTransformer(polygon, args)
    clipping = Clip(polygon, args, twoDtransformer, threeDtransformer, args.projection)

    rendered = clipping.z_buffering(polygon)

    fileio.write_ppm(rendered, args)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-f", "--red_file", type=str, default="bound-sprellpsd.smf")
    parser.add_argument("-g", "--green_file", type=str)
    parser.add_argument("-i", "--blue_file", type=str)

    parser.add_argument("-j", "--lb_viewportx", type=int, default=0)
    parser.add_argument("-k", "--lb_viewporty", type=int, default=0)
    parser.add_argument("-o", "--ub_viewportx", type=int, default=500)
    parser.add_argument("-p", "--ub_viewporty", type=int, default=500)

    parser.add_argument("-x", "--x_prp", type=float, default=0.0)
    parser.add_argument("-y", "--y_prp", type=float, default=0.0)
    parser.add_argument("-z", "--z_prp", type=float, default=1.0)

    parser.add_argument("-X", "--x_vrp", type=float, default=0.0)
    parser.add_argument("-Y", "--y_vrp", type=float, default=0.0)
    parser.add_argument("-Z", "--z_vrp", type=float, default=0.0)

    parser.add_argument("-q", "--x_vpn", type=float, default=0.0)
    parser.add_argument("-r", "--y_vpn", type=float, default=0.0)
    parser.add_argument("-w", "--z_vpn", type=float, default=-1.0)

    parser.add_argument("-Q", "--x_vup", type=float, default=0.0)
    parser.add_argument("-R", "--y_vup", type=float, default=1.0)
    parser.add_argument("-W", "--z_vup", type=float, default=0.0)

    parser.add_argument("-u", "--umin_vrc", type=float, default=-0.7)
    parser.add_argument("-v", "--vmin_vrc", type=float, default=-0.7)
    parser.add_argument("-U", "--umax_vrc", type=float, default=0.7)
    parser.add_argument("-V", "--vmax_vrc", type=float, default=0.7)

    # perspective projection if false (not present), parallel if true (is present)
    parser.add_argument("-P", "--projection", action="store_true")
    
    parser.add_argument("-F", "--front_clipping", type=float, default=0.6)
    parser.add_argument("-B", "--back_clipping", type=float, default=-0.6)

    args = parser.parse_args()

    hw5(args)

if __name__ == "__main__":
    main()