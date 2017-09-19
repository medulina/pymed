from flask import Flask, render_template, request, current_app,  send_from_directory, jsonify
from werkzeug import secure_filename
import os
from generate_tiles import create_tiles, save_json_pretty
from nipype.utils.filemanip import load_json
from glob import glob
import base64
import numpy as np
import nibabel as nib
from surface import create_vtk

app = Flask(__name__)
# Got from https://www.tutorialspoint.com/flask/flask_file_uploading.htm

# Send the index.html file
@app.route('/')
def main():
    return send_from_directory("web/",'index.html')

@app.route('/subjects')
def up():
    return send_from_directory("web/",'subjects.html')

# Send any js/ css/ files
@app.route('/<path:ptype>/<path:pfile>')
def send_file(ptype, pfile):
    return send_from_directory(os.path.join("web", ptype) ,pfile)

@app.route('/uploads/<path:pfile>')
def send_manifest(pfile):
    return send_from_directory("uploads", pfile)

@app.route('/uploads/<path:pfile>/<path:item>')
def send_iamges(pfile, item):
    return send_from_directory("uploads", os.path.join(pfile, item))

@app.route('/tiles/pngs/<subject_id>')
def send_pngs(subject_id):
    pngs = sorted(glob(os.path.join("tiles", subject_id, "*", "*.png")))
    data = {"ax": [], "sag": [], "cor": []}
    for p in pngs:
        entry = {}
        sd = p.split("/")[-2]
        sliceNo = p.split("/")[-1].replace(".png", "").split("_")[-1]
        with open(p, 'rb') as img:
            encoded_string = base64.b64encode(img.read()).decode('utf-8')
            entry["slice"] = sliceNo
            entry["png"] = encoded_string
            entry["sliceNice"] = "%03d" % int(sliceNo)
        data[sd].append(entry)


    return jsonify(data)

def dict2arr(image_data, mask_data):
    mask_arr = np.zeros((image_data.shape[0], image_data.shape[1]))
    for ikey, vald in mask_data.items():
        for jkey, val in vald.items():
            mask_arr[int(jkey), int(ikey)] = val
    return mask_arr

@app.route('/getAggNii', methods = ['POST'])
def getAggNii():
    data = request.json

    # find our subject and their base image
    subject = data[0]["subject"]
    subject_nii_file = [b for b in glob("uploads/{}/*.nii.gz".format(subject)) if "base" in b][0]
    subject_mask_file = [b for b in glob("uploads/{}/*.nii.gz".format(subject)) if "mask" in b][0]

    # load image and convert to IPL
    img_data = nib.load(subject_nii_file)
    aff = img_data.affine
    orientation = nib.orientations.io_orientation(aff)
    print("original image orientation is", "".join(nib.orientations.aff2axcodes(aff)))
    print("now converting to IPL")
    def toIPL(data):
        data_RAS = nib.orientations.apply_orientation(data, orientation) #In RAS
        return nib.orientations.apply_orientation(data_RAS, nib.orientations.axcodes2ornt("IPL")) #IPL is its own inverse

    def fromIPL(data):
        xfm = nib.orientations.ornt_transform(nib.orientations.axcodes2ornt("IPL"), orientation)
        return nib.orientations.apply_orientation(data,xfm)

    data_IPL = toIPL(img_data.get_data())
    slicer = {"ax": 0, "cor": 1, "sag": 2}

    #create a new image with data
    crowd_data = np.zeros(data_IPL.shape)
    for d in data:
        all_data_slicer = [slice(None), slice(None), slice(None)]
        all_data_slicer[slicer[d["slice_direction"]]] = d["slice"]
        crowd_data[all_data_slicer] = dict2arr(crowd_data[all_data_slicer], d["agg"])

    # save the Nifti1Imag
    # TODO: this affine is WRONG! AK FIX!!

    crowd_data = fromIPL(crowd_data)

    out_file = os.path.join("uploads", subject, "crowd.nii.gz")
    nib.Nifti1Image(crowd_data, aff).to_filename(out_file)

    #surface stuff
    out_vtk = out_file.replace(".nii.gz", ".vtk")
    create_vtk(out_file, out_vtk)

    out_truth_vtk = subject_mask_file.replace(".nii.gz", ".vtk")
    create_vtk(subject_mask_file, out_truth_vtk)

    return out_file



# Function to create tiles on upload
@app.route('/tiler', methods = ['POST'])
def tile_function():

    if request.method == 'POST':

        upload_path = 'uploads/'
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)

        json_path = os.path.join(upload_path, 'uploads.json')

        if os.path.exists(json_path):
            upload_manifest = load_json(json_path)
        else:
            upload_manifest = []
        print("hello", request.files)
        f_image = request.files['image_file']
        f_mask = request.files['mask_file']
        slice_direction = request.form['slice_direction']

        min_Nvox = request.form['min_Nvox']
        ptid = request.form['patient_id']

        fname_image = os.path.basename(secure_filename(f_image.filename))
        fname_mask = os.path.basename(secure_filename(f_mask.filename))



        #Save images in upload directory
        base_path = os.path.join(upload_path, ptid)
        if not os.path.exists(base_path):
            os.makedirs(base_path)

        image_savepath = os.path.join(base_path, ptid+'_base.nii.gz')
        mask_savepath = os.path.join(base_path, ptid+'_mask.nii.gz')
        f_image.save(image_savepath)
        f_mask.save(mask_savepath)

        entry = {'subject_id': ptid,
               'mask_filename': secure_filename(f_mask.filename),
               'image_filename': secure_filename(f_image.filename),
               'mask_server_path': mask_savepath,
               'image_server_path': image_savepath,
               'voxel_threshold': min_Nvox,
               'slice_direction': slice_direction}
        print(entry)


        #Make the json entry
        upload_manifest.append(entry)

        #create tiles from the nifti image and save in tile directory
        create_tiles(image_savepath, mask_savepath, slice_direction,
                   os.path.join('tiles', ptid, slice_direction),
                   int(min_Nvox), 1, False, None)


        save_json_pretty(os.path.join(upload_path,'uploads.json'), upload_manifest)
        print(upload_manifest)
        if len(fname_image) > 0 and len(fname_mask) >0:
            return jsonify({"subjects": upload_manifest})
        else:
            return "Error: Please upload a valid file"

def update_manifest(vthresh=100):
    subjects = [s.split("/")[-1] for s in glob("uploads/*")]
    manifest = []
    for s in subjects:
        imgs = glob(os.path.join("uploads", s, "*"))
        tiles = glob(os.path.join("tiles",s,"*"))
        tile_dirs = [t.split("/")[-1] for t in tiles]
        mask = [m for m in imgs if "mask" in m][0]
        base = [b for b in imgs if "base" in b][0]

        entry = {'subject_id': s,
               'mask_filename': mask,
               'image_filename': base,
               'mask_server_path': mask,
               'image_server_path': base,
               'voxel_threshold': vthresh,
               'slice_direction': ",".join(tile_dirs)}
        manifest.append(entry)

    save_json_pretty(os.path.join("uploads",'uploads.json'), manifest)
    print("updated for subs", " ".join(subjects))


if __name__ == '__main__':
   #app.config['UPLOAD_FOLDER'] = "uploads/"

   #if not os.path.exists(app.config['UPLOAD_FOLDER']):
   #    os.makedirs(app.config['UPLOAD_FOLDER'])

   app.run(port=8000, debug=True)
