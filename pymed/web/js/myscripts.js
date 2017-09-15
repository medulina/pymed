// register the grid component
Vue.component('demo-grid', {
  template: '#grid-template',
  props: {
    data: Array,
    columns: Array,
    filterKey: String
  },
  data: function () {
    var sortOrders = {}
    this.columns.forEach(function (key) {
      sortOrders[key] = 1
    })
    return {
      sortKey: '',
      sortOrders: sortOrders
    }
  },
  computed: {
    filteredData: function () {
      var sortKey = this.sortKey
      var filterKey = this.filterKey && this.filterKey.toLowerCase()
      var order = this.sortOrders[sortKey] || 1
      var data = this.data
      if (filterKey) {
        data = data.filter(function (row) {
          return Object.keys(row).some(function (key) {
            return String(row[key]).toLowerCase().indexOf(filterKey) > -1
          })
        })
      }
      if (sortKey) {
        data = data.slice().sort(function (a, b) {
          a = a[sortKey]
          b = b[sortKey]
          return (a === b ? 0 : a > b ? 1 : -1) * order
        })
      }
      return data
    }
  },
  filters: {
    capitalize: function (str) {
      return str.charAt(0).toUpperCase() + str.slice(1)
    }
  },
  methods: {
    sortBy: function (key) {
      this.sortKey = key
      this.sortOrders[key] = this.sortOrders[key] * -1
    }
  }
})

Vue.component('upload-form', {
  template: '#uploadForm',
  props: [],
})

var app = new Vue({
  el: "#main",
  data: {
    subjects: [],
    search: "",
    currentSubject: {},
    columns: ['subject_id', 'slice_direction',
              'voxel_threshold', 'image_filename',
              'mask_filename',],
    currentTiles: {},
    pviewer_params: {},
    allslices: []
  },
  methods: {
    showPapaya: function(){
      var subject_obj = this.currentSubject
      params = [];
      params["worldSpace"] = false;
      params["showControls"] = false;
      params["radiological"] = true;
      params["images"] = [subject_obj.image_server_path, subject_obj.mask_server_path];
      var name = subject_obj.mask_server_path
      var split_name = name.split("/")
      split_name = split_name[split_name.length-1]
      params[split_name] = {lut: "Overlay (Positives)", alpha: 0.5, min: 0, max:1.1}
      papaya.Container.addViewer("viewer", params)
      papaya.Container.allowPropagation = true;
    },
    setSubject: function(subject_obj){
      this.currentSubject = subject_obj
      this.allslices = []
      a.remove("subject_id")
      a.set("subject_id", subject_obj.subject_id)
      //a.go(;
      window.history.pushState({path:a.url},'',a.url);
      load_tiles(subject_obj.subject_id)
      this.showPapaya()
      this.getAllAgg()

    },
    getAllAgg: function(){

      for (key in this.currentTiles){
        this.currentTiles[key].forEach(function(val, idx, arr){
          get_mindR_info("meningioma001",
                         app.currentSubject.subject_id,
                         key,val.slice,
                         function(d){
                           get_maskagg(d, function(stat){app.allslices.push(stat)})
                         });
        });
      }
    },
    sendAggtoServer: function(){
      $.ajax({
         type : "POST",
         url : "/getAggNii",
         data: JSON.stringify(this.allslices, null, '\t'),
         contentType: 'application/json;charset=UTF-8',
         success: function(result) {
             console.log(result);
             papaya.Container.addImage(papayaContainers.length - 1,
               result, {"crowd.nii.gz": {"min": 0, "max": 10, alpha: 0.5, "lut": "Red Overlay"}}
             )
         }
      });
    }
  },
});

$('#upload_form').on("submit", function(e) {
    var formData = new FormData($("form")[0]);
    console.log("onsubmit formData is", formData)
    $.ajax({
        url: "/tiler",
        type: 'POST',
        data: formData,
        async: false,
        success: function (data) {
            console.log(data)
            app.subjects = data.subjects
        },
        cache: false,
        contentType: false,
        processData: false
    });

    return false;
});

function update_manifest(){
  $.getJSON("/uploads/uploads.json", function(data){
    app.subjects = data
    Object.keys(params).indexOf("subject_id") >= 0 ? set_subject(params["subject_id"]) : null
    app.subjects.forEach(function(val, idx, arr){
      $.get('https://api.medulina.com/api/v1/image/?where={"task":"meningioma001", "subject":"'+val.subject_id+'"}',
      function(d){
        app.subjects[idx].server_tile_count = d._meta.total;
        console.log(app.subjects[idx].subject_id,   app.subjects[idx].server_tile_count)
      })
    });
  })
}

update_manifest()

var a = new QS()
var params = a.getAll()

function set_subject(subject_id){
  var sub = _.find(app.subjects, function(v){
    return v.subject_id == subject_id ? v: null
  })
  app.currentSubject = sub
  load_tiles(subject_id)
  app.showPapaya()
}

function load_tiles(subject_id){
  $.get("/tiles/pngs/"+subject_id, function(data){
  	console.log(data)
    app.currentTiles = data
    app.getAllAgg()
  })
}

function get_mindR_info(task, subject_id, slice_direction, slice, callback){
  var url = 'https://api.medulina.com/api/v1/image/?where='
  var query = '{"task": "TASK", "subject": "SUBJECT_ID", "slice_direction": "SLICE_DIRECTION", "slice": SLICE}'
  query = query.replace("TASK", task)
       .replace("SLICE_DIRECTION", slice_direction)
       .replace("SUBJECT_ID", subject_id)
       .replace("SLICE", slice)
  $.get(url+query,function(data){
    //console.log("got it:", data)
    if (data._items.length == 1){
      callback(data._items[0])
    }
    else if (data._items.length == 0) {
      console.log("THERE ARE MULTIPLE ENTRIES")
    }
    else {
      console.log("COULD NOT FIND")
    }
  })
}

function get_maskagg(image_entry, callback){
  //console.log("image_entry", image_entry)
  var url = 'https://api.medulina.com/api/v1/maskagg/?aggregate={"$image_search":"' + image_entry._id + '"}'
  $.get(url, function(data){
    //console.log("got agg, ", data)
    var to_server = {
      agg: data.mask_sum,
      slice: image_entry.slice,
      slice_direction: image_entry.slice_direction,
      subject: image_entry.subject,
    }
    callback(to_server)
  })
}
