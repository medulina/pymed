def march_the_cubes(data, aff):
    from skimage.measure import marching_cubes
    import numpy as np
    from dipy.tracking.utils import move_streamlines
    verts, faces, _, _ = marching_cubes(data, level=0.5)
    verts = np.asarray(list(move_streamlines(verts, aff)))
    #TODO: apply affine here
    return verts, faces



from mindboggle.mio.vtks import read_vtk, write_vtk

def get_surface(fname):
    import nibabel as nib
    from skimage.measure import marching_cubes
    import numpy as np
    from dipy.tracking.utils import move_streamlines

    img = nib.load(fname)
    data, aff = img.get_data(), img.affine

    verts, faces, normals, values = marching_cubes(data, level=0.5)
    verts = np.asarray(list(move_streamlines(verts, aff)))
    return verts, faces


def create_vtk(in_file, out_file):

    verts, faces = get_surface(in_file)
    write_vtk(out_file, points = verts, faces = faces)
    return out_file
