{% extends "base.tpl" %}
{% block title %}Upload Data (organized in columns){% endblock %}
{% block content %}

  <h1>Upload a table as a new
    {% if new_version %} 
      version of an existing dataset
    {% else %}
      dataset
    {% endif %}
  </h1>

  <h4>Data submissions</h4>
  <p>The entire contents of Taiga are technically accessibly the Broad community, so keep that in mind when uploading data.  If data is unpublished, you can indicate it as such with the "Publish status" field on the form below and we rely on all users to treat the data accordingly.</p>
  
  <h4>Data format</h4>
  <p>
    This form can be used to create a new dataset from a tab-delimited text file.   The first row in the file will be interpreted as the column names, which must be unique.   Each column will be mapped to a single type (integers, floats, or text) independantly.  If a column contains a mixture of types, the entire column will be treated as the more permissive type.  For example, if the column contains numbers and text, the entire column will be treated as text.
  </p>

  <form class="form-horizontal" role="form" method="post" action="/upload/columnar" enctype="multipart/form-data">
    {% if new_version %} 
      <input type="hidden" name="overwrite_existing" value="true">
      <input type="hidden" name="name" value="{{name}}">
      <input type="hidden" name="overwrite_existing" value="true">
    {% endif %}
    <div class="form-group">
      <label for="inputName" class="col-sm-2 control-label">Dataset Name</label>
      <div class="col-sm-10">
        {% if new_version %}
          <input type="text" disabled value="{{name}}" class="form-control" id="inputName" placeholder="Name">
        {% else %}
          <input type="text" class="form-control" id="inputName" placeholder="Name" name="name">
        {% endif %}
      </div>
    </div>

    <div class="form-group">
      <label for="publishState" class="col-sm-2 control-label">Publish status</label>
      <div class="col-sm-2">
        <select class="form-control" id="publishedState" name="is_published">
          <option selected value="False">Unpublished</option>
          <option value="True">Published</option>
        </select>
      </div>
    </div>

    <div class="form-group">
      <label for="inputDescription" class="col-sm-2 control-label">Description</label>
      <div class="col-sm-10">
        <textarea id="inputDescription" class="form-control" rows="3" name="description">{{description}}</textarea>
      </div>
    </div>
    <div class="form-group">
      <label for="inputFile" class="col-sm-2 control-label">File</label>
      <div class="col-sm-10">
        <input type="file" class="form-control" id="inputFile" name="file">
      </div>
    </div>
    <div class="form-group">
      <div class="col-sm-offset-2 col-sm-10">
        <button type="submit" class="btn btn-default">Submit</button>
      </div>
    </div>
  </form>

{% endblock %}

{% block scripts %}
<script>
$(document).ready(function () {
  
  var existing_data_types = {{ existing_data_types }}
  
  $('#inputDataType').select2({
    query: function (query){
          var data = {results: []};
 
          $.each(existing_data_types, function(){
              if(query.term.length == 0 || this.toUpperCase().indexOf(query.term.toUpperCase()) >= 0 ){
                  data.results.push({id: this, text: this });
              }
          });

          if(data.results.length == 0) {
            data.results.push({id: query.term, text: query.term})
          }

          query.callback(data);
      }
  });
});
</script>
{% endblock %}
