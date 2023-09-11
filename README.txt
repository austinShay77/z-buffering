My submission is programmed in python 3.8.10 on the drexel tux linux servers.

My source code is in CG_hw5.py, but I put my code in an executable file call CG_hw5 that can be called
as needed in the requirements.

fileIO.py:

    lines 22 - 32
    writeppm(lines) -   Reads in the frame buffer and writes it to stdout.

transformer.py:

    Within my perspective transformations I appended the z value prior to converting to 2d from 3d.

CG_hw5.py:

    lines 41 - 67
    z_buffering(polygons) - Takes in all the read models and loops over them. I perform a scanline operation.
                            At each scan line, I find the intersecting points and their corresponding z_a and z_b values using 
                            the z interpolation shown in class. From that same scan line I also do a z interpolation that updates
                            the buffers based on the calculated z value across the scan line.

    lines 69 - 90
    z_interpolation(x_range, z_buf, f_buf, y, color_index) -    Takes in the buffers, the current color of the model, the current scan line
                                                                and the intersecting x values with their z values. It loops over every x value
                                                                in between the the intersections and calculates that z_p. From that z_p I update
                                                                the buffers if it passes the conditions necessary.

    lines 163 - 167
    I added code to calculate the z value at that intersecting point.