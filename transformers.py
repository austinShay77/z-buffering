import math
import numpy as np 

def _normalize(vector):
    new_vector = []
    magnitude = 0
    for i in vector:
        magnitude += i**2
    magnitude = math.sqrt(magnitude)
    for i in vector:
        new_vector.append(i/magnitude)
    return new_vector

class Coordinates:
    def __init__(self):
        self.x1 = 0
        self.y1 = 0
        self.x2 = 0
        self.y2 = 0

    # uses the current line to re-assign attributes
    def _set_points(self, line):
        if "Line" in line:
            self.x1, self.y1 = float(line[0]), float(line[1])
            self.x2, self.y2 = float(line[2]), float(line[3])
        elif "moveto" in line or "lineto" in line:
            self.x1, self.y1 = float(line[0]), float(line[1])
        elif len(line) == 2:
            self.x1, self.y1 = float(line[0]), float(line[1])
        else:
            self.x1, self.y1 = float(line[0]), float(line[1])

class ThreeDTransformer(Coordinates):
    def __init__(self, faces, args):
        self.faces = faces
        self.vrp_x = args.x_vrp
        self.vrp_y = args.y_vrp
        self.vrp_z = args.z_vrp

        self.vpn_x = args.x_vpn
        self.vpn_y = args.y_vpn
        self.vpn_z = args.z_vpn

        self.vup_x = args.x_vup
        self.vup_y = args.y_vup
        self.vup_z = args.z_vup

        self.prp_x = args.x_prp
        self.prp_y = args.y_prp
        self.prp_z = args.z_prp

        self.u_max = args.umax_vrc
        self.u_min = args.umin_vrc
        self.v_max = args.vmax_vrc
        self.v_min = args.vmin_vrc

        self.F = args.front_clipping
        self.B = args.back_clipping

        self.d = args.z_prp/(args.back_clipping - args.z_prp)

    def parallel_normalization(self):
        new_P = []

        inside = np.dot(self._rotate(), self._translate([self.vrp_x, self.vrp_y, self.vrp_z]))
        next = np.dot(self._shear(), inside)
        after = np.dot(self._translate_parallel(), next)
        n_par = np.dot(self._scale_parallel(), after)

        first_vertice = []
        is_first_vertice = True
        for face in self.faces:
            if face != "new model":
                for vertice in face:
                    converted = [float(i) for i in vertice]
                    new_vertices = np.dot(n_par, converted)
                    if is_first_vertice:
                        first_vertice.append([new_vertices[0], new_vertices[1], converted[2]])
                        new_P.append([new_vertices[0], new_vertices[1], converted[2]])
                        is_first_vertice = False
                    else:
                        new_P.append([new_vertices[0], new_vertices[1], converted[2]])
                new_P.append(first_vertice[0])
                new_P.append(["stroke"])
                is_first_vertice = True
                first_vertice = []
            else:
                new_P.append(["new model"])
        return new_P

    def perspective_normalization(self):
        new_P = []

        inside = np.dot(self._rotate(), self._translate([self.vrp_x, self.vrp_y, self.vrp_z]))
        next = np.dot(self._translate([self.prp_x, self.prp_y, self.prp_z]), inside)
        after = np.dot(self._shear(), next)
        n_per = np.dot(self._scale_perspective(), after)

        first_vertice = []
        is_first_vertice = True
        for face in self.faces:
            # print(face) 
            if face != "new model":
                for vertice in face:
                    # print(vertice)
                    converted = [float(i) for i in vertice]
                    new_vertices = np.dot(n_per, converted)
                    if new_vertices[2] != 0:
                        x_prime = new_vertices[0]/(new_vertices[2]/abs(self.d))
                        y_prime = new_vertices[1]/(new_vertices[2]/abs(self.d))
                    else:
                        x_prime = 0
                        y_prime = 0
                    if is_first_vertice:
                        first_vertice.append([x_prime, y_prime, converted[2]])
                        new_P.append([x_prime, y_prime, converted[2]])
                        is_first_vertice = False
                    else:
                        new_P.append([x_prime, y_prime, converted[2]])
                new_P.append(first_vertice[0])
                new_P.append(["stroke"])
                is_first_vertice = True
                first_vertice = []
            else:
                new_P.append(["new model"])
        return new_P

    def _translate(self, vector): # vector must be in [x, y, z] form
        t = [
            [1, 0, 0, -vector[0]],
            [0, 1, 0, -vector[1]],
            [0, 0, 1, -vector[2]], 
            [0, 0, 0, 1]
            ]
        # print("translate\n",np.array(t))
        return np.array(t)

    def _translate_parallel(self):
        t_par = [
                [1, 0, 0, -((self.u_max + self.u_min))/2],
                [0, 1, 0, -((self.v_max + self.v_min))/2],
                [0, 0, 1, -self.F],
                [0, 0, 0, 1]
                ]
        return np.array(t_par)

    def _rotate(self):
        r_z = _normalize([self.vpn_x, self.vpn_y, self.vpn_z])
        r_x = _normalize(np.cross([self.vup_x, self.vup_y, self.vup_z], r_z))
        r_y = np.cross(r_z, r_x)

        r = [
            [r_x[0], r_x[1], r_x[2], 0],
            [r_y[0], r_y[1], r_y[2], 0],
            [r_z[0], r_z[1], r_z[2], 0],
            [0, 0, 0, 1]
            ]
        # print("rotate\n", np.array(r))
        return np.array(r)

    def _shear(self):
        # prp = [self.prp_x, self.prp_y, self.prp_z]
        # cw = [(self.u_max + self.u_min)/2, (self.v_max + self.v_min)/2, 0]
        # dop = np.subtract(cw, prp)
        # sh_x = -(dop[0] / dop[2])
        # sh_y = -(dop[1] / dop[2])

        # sh = [
        #     [1, 0, sh_x, 0],
        #     [0, 1, sh_y, 0],
        #     [0, 0, 1, 0],
        #     [0, 0, 0, 1]
        #     ]
        sh = [
            [1, 0, ((1/2)*(self.u_max + self.u_min) - self.prp_x)/self.prp_z, 0],
            [0, 1, ((1/2)*(self.v_max + self.v_min) - self.prp_y)/self.prp_z, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ]
        # print("shere\n", np.array(sh))
        return np.array(sh)

    def _scale_parallel(self):
        s_par = [
                [2/(self.u_max - self.u_min), 0, 0, 0],
                [0, 2/(self.v_max - self.v_min), 0, 0],
                [0, 0, 1/(self.F - self.B), 0],
                [0, 0, 0, 1]
                ]
        return np.array(s_par)

    def _scale_perspective(self):
        # print(f"prpn {self.prp_z}, umax {self.u_max}, umin {self.u_min}, b {self.B}")
        s_per = [
                [(2*self.prp_z)/((self.u_max - self.u_min)*(self.prp_z - self.B)), 0, 0, 0],
                [0, (2*self.prp_z)/((self.v_max - self.v_min)*(self.prp_z - self.B)), 0, 0],
                [0, 0, 1/(self.prp_z - self.B), 0],
                [0, 0, 0, 1]
                ]
        # print("scale perspective\n", np.array(s_per))
        return np.array(s_per)


class TwoDTransformer(Coordinates):
    def __init__(self, lines, args):
        super().__init__()
        self.lines = lines
        self.args = args

    # create a new list of transformed lines
    def transform_lines(self):
        new_lines = []
        for line in self.lines:
            if "stroke" in line:
                new_lines.append(line)
            else:
                self._set_points(line)
                self._scale()
                self._rotate()
                self._translate()
                if "Line" in line:
                    new_lines.append([self.x1, self.y1, self.x2, self.y2, line[4]])
                elif "moveto" in line or "lineto" in line:
                    new_lines.append([self.x1, self.y1, line[2]])
        return new_lines

    def _scale(self, x_scale = None, y_scale = None):
        if x_scale is None and y_scale is None:
            self.x1 = self.x1 * self.args.scaling_factor
            self.y1 =  self.y1 * self.args.scaling_factor

            self.x2 = self.x2 * self.args.scaling_factor
            self.y2 =  self.y2 * self.args.scaling_factor
        else:
            self.x1 = self.x1 * x_scale
            self.y1 = self.y1 * y_scale

    def _rotate(self):
        phi = self.args.ccr * math.pi / 180
        x1 = self.x1 * math.cos(phi) - self.y1 * math.sin(phi)
        y1 = self.x1 * math.sin(phi) + self.y1 * math.cos(phi)
        x2 = self.x2 * math.cos(phi) - self.y2 * math.sin(phi)
        y2 = self.x2 * math.sin(phi) + self.y2 * math.cos(phi)

        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2
    
    def _translate(self, x_dim = None, y_dim = None):
        if x_dim is None and y_dim is None:
            self.x1 += self.args.x_dim
            self.y1 += self.args.y_dim

            self.x2 += self.args.x_dim
            self.y2 += self.args.y_dim
        else:
            self.x1 += x_dim
            self.y1 += y_dim