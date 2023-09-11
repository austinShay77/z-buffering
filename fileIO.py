import sys

class FileIO:
    def __init__(self, red_path, green_path = None, blue_path = None):
        self.red_path = red_path
        self.green_path = green_path
        self.blue_path = blue_path
    
    def write_pbm(self, lines, args):
        new_line = 1
        sys.stdout.write(f"P1\n# {args.file[:-3]}.pbm\n{501} {501}\n")
        lines.reverse()
        for row in lines:
            for col in row:
                if new_line == 70:
                    print(col, end="\n")
                    new_line = 1
                    continue
                print(col, end=" ")
                new_line += 1

    def write_ppm(self, lines, args):
        new_line = 1
        sys.stdout.write(f"P3\n# output.ppm\n{501} {501}\n255\n")
        for row in lines:
            for col in row:
                if new_line == 70:
                    print(col, end="\n")
                    new_line = 1
                    continue
                print(col, end="\t")
                new_line += 1

    # take a list of lines, write them to stdout in .ps form
    def write_ps(self, lines, args):
        is_moveto = True

        sys.stdout.write(f"%%BeginSetup\n   << /PageSize [{501} {501}] >> setpagedevice\n%%EndSetup\n\n%%%BEGIN")
        for line in lines:
            if "stroke" not in line:
                x = round(line[0])
                y = round(line[1])
                if is_moveto:
                    sys.stdout.write(f"\n{x} {y} moveto")
                    is_moveto = False
                else:
                    sys.stdout.write(f"\n{x} {y} lineto")
            elif "stroke" in line:
                sys.stdout.write(f"\n{line[0]}")
                is_moveto = True
                
        sys.stdout.write(f"\n%%%END\n")

    # take a .ps file, parse it into a 2d array
    def read(self):
        with open(self.red_path) as file:
            commands = self._find_meaningful_lines([line.rstrip() for line in file if line != "\n"])
        return self._split_lines(commands)

    def read_smf(self):
        files = [self.red_path, self.green_path, self.blue_path]
        vertices = []
        faces = []
        for path in files:
            if path is not None:
                faces.append("new model")
                with open(path) as file:
                    for line in file:
                        working_line = line.rstrip().split(" ")
                        # set vertices as homogenous
                        if working_line[0] == "v":
                            working_line.append(1)
                            vertices.append(working_line[1:])
                        # use vertices to have list of faces in counter-clockwise order
                        if working_line[0] == "f":
                            faces.append([vertices[int(working_line[1])-1], vertices[int(working_line[2])-1], vertices[int(working_line[3])-1]])
        return faces
    
    # splites the line so each coordinate is its own element
    def _split_lines(self, commands):
        organized = [element.split() for element in commands]
        return organized

    # only keeps lines after %%%BEGIN and before %%%END
    def _find_meaningful_lines(self, commands):
        meaningless = True
        meaningful_lines = []
        for element in commands:
            if meaningless:
                if f"%%%BEGIN" in element:
                    meaningless = False
            else:
                if f"%%%END" in element:
                    break
                meaningful_lines.append(element)
        return meaningful_lines

