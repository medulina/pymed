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
    columns: ['subject_id', 'slice_direction',
              'voxel_threshold', 'image_filename',
              'mask_filename',],
  }
})

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
  })
}

update_manifest()

// bootstrap the demo
var demo = new Vue({
  el: '#demo',
  data: {
    searchQuery: '',
    gridColumns: ['name', 'power'],
    gridData: [
      { name: 'Chuck Norris', power: Infinity },
      { name: 'Bruce Lee', power: 9000 },
      { name: 'Jackie Chan', power: 7000 },
      { name: 'Jet Li', power: 8000 }
    ]
  }
})
