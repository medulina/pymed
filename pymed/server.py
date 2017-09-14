from flask import Flask, render_template, request, current_app,  send_from_directory, jsonify
from werkzeug import secure_filename
import os
from generate_tiles import create_tiles, save_json_pretty
from nipype.utils.filemanip import load_json

app = Flask(__name__)
# Got from https://www.tutorialspoint.com/flask/flask_file_uploading.htm

# Send the index.html file
@app.route('/')
def main():
   return send_from_directory("web/",'index.html')

# Send any js/ css/ files
@app.route('/<path:ptype>/<path:pfile>')
def send_file(ptype, pfile):
   return send_from_directory(os.path.join("web", ptype) ,pfile)

@app.route('/uploads/<path:pfile>')
def send_manifest(pfile):
   return send_from_directory("uploads", pfile)

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

        image_savepath = os.path.join(base_path, ptid+'_image.nii.gz')
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

if __name__ == '__main__':
   #app.config['UPLOAD_FOLDER'] = "uploads/"

   #if not os.path.exists(app.config['UPLOAD_FOLDER']):
   #    os.makedirs(app.config['UPLOAD_FOLDER'])

   app.run(port=8000, debug=True)
